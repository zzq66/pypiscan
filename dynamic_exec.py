#!/usr/bin/env python3
#尽可能地执行包里面的每一个函数和实例化类，用于动态测试，可以搭配云沙箱等工具联合使用。
import os
import importlib
import inspect
import os.path
import signal
import subprocess
import sys
import traceback
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import dataclass
from importlib.metadata import files
from typing import Optional
from unittest.mock import MagicMock

PY_EXTENSION = '.py'

EXECUTION_LOG_PATH = '/tmp/execution.log'
EXECUTION_TIMEOUT_SECONDS = 1000

@dataclass
class Package:
    """Class for tracking a package."""
    name: str
    version: Optional[str] = None
    local_path: Optional[str] = None

    def install_arg(self) -> str:
        if self.local_path:
            return self.local_path
        elif self.version:
            return f'{self.name}=={self.version}'
        else:
            return self.name


def install(package):
    """Pip install."""
    arg = package.install_arg()
    try:
        output = subprocess.check_output(
            (sys.executable, '-m', 'pip', 'install', '--pre', arg),
            stderr=subprocess.STDOUT)
        print('Install succeeded:')
        print(output.decode())
    except subprocess.CalledProcessError as e:
        print('Failed to install:')
        print(e.output.decode())
        raise


def path_to_import(path):
    """Convert a path to import."""
    if path.name == '__init__.py':
        import_path = str(path.parent)
    else:
        #print(str(path))
        import_path = (str(path)).split('.')[0]
        #(str(path)).rstrip(PY_EXTENSION)

    return import_path.replace('/', '.')


def import_package(package):
    """Import phase for analyzing the package."""
    print(files(package.name))
    all_path = files(package.name)
    for path in all_path:
        # TODO: pyc, C extensions?
        if path.suffix != PY_EXTENSION:
            continue
        #print(path)
        import_path = path_to_import(path)
        import_module(import_path)


def import_single_module(import_path):
    module_dir = os.path.dirname(import_path)
    sys.path.append(module_dir)
    module_name = os.path.basename(import_path).rstrip(PY_EXTENSION)
    print(f'Import single module at {import_path}')
    import_module(module_name)


def import_module(import_path):
    print('Importing', import_path)
    try:
        module = importlib.import_module(import_path)
    except:
        print('Failed to import', import_path)
        traceback.print_exc()
        return
    # only run package execution if the log file exists
    if not os.path.exists(EXECUTION_LOG_PATH):
        return

# 模块执行的设置 
# 1. 函数执行超时告警的处理程序 
# 2. 将标准输出和标准错误重定向到执行日志文件
    signal.signal(signal.SIGALRM, handler=alarm_handler)
    with open(EXECUTION_LOG_PATH, 'a+') as log, redirect_stdout(log), redirect_stderr(log):
        try:
            execute_module(module)
        except:
            print('Failed to execute code for module', import_path)
            traceback.print_exc()

    # restore default signal handler for SIGALRM
    signal.signal(signal.SIGALRM, signal.SIG_DFL)


def execute_module(module):
    """Best-effort execution of code in a module"""
    print('[module]', module)
#  跟踪到目前为止我们在返回值中看到的属于模块的所有类型， 
# 这样我们就可以递归地探索每个方法而不用进入无限循环。 
# 使用模块代码返回的实例可能比使用实例更有用 
# 用模拟的构造函数参数实例化
    seen_types = set()

    def should_investigate(t):
        return t.__module__ == module.__name__ and t not in seen_types

    def mark_seen(t):
        seen_types.add(t)

    instantiated_types = set()

    skipped_names = []
    for (name, member) in inspect.getmembers(module):
        if inspect.isfunction(member):
            return_value = try_invoke_function(member, name)
            return_type = return_value.__class__
            # TODO should it be DFS or BFS?
            if should_investigate(return_type):
                print('[investigate type]', return_type)
                mark_seen(return_type)
                #try_call_methods(return_value, return_type, should_investigate, mark_seen)
        elif inspect.isclass(member):
            instance = try_instantiate_class(member, name)
            assert instance.__class__ == member
            if instance is not None and member not in instantiated_types:
                instantiated_types.add(member)
                try_call_methods(instance, name, should_investigate, mark_seen)
        else:
            skipped_names.append(name)

    print('[skipped members]', ' '.join(skipped_names))


def alarm_handler(sig_num, frame):
    raise TimeoutError('Timeout exceeded for function execution')


# 根据声明的签名调用带有模拟参数的函数。 
# 参数类型为MagicMock，其实例将返回 
# 对其调用的任何方法的假值。 
# 异常必须由调用方处理。
def invoke_function(obj):
    signature = inspect.signature(obj)
    args = []
    kwargs = {}

    for name, param in signature.parameters.items():
        # use MagicMock to create semi-realistic function argument values
        # https://docs.python.org/3/library/unittest.mock.html
        value = MagicMock() if param.default == param.empty else param.default
        match param.kind:
            case param.POSITIONAL_ONLY:
                args.append(value)
            case param.KEYWORD_ONLY | param.POSITIONAL_OR_KEYWORD:
                kwargs[name] = value
            case param.VAR_POSITIONAL:  # when *args appears in signature
                pass  # ignore
            case param.VAR_KEYWORD:  # when **args appears in signature
                pass  # ignore

    # 绑定参数并调用函数
    # 任何异常都将传播给调用方
    bound = signature.bind(*args, **kwargs)

    # 超时运行以防止挂起
    signal.alarm(EXECUTION_TIMEOUT_SECONDS)
    ret = obj(*bound.args, **bound.kwargs)
    signal.alarm(0)
    return ret


#执行一个可调用程序并捕获任何异常，将日志记录到标准输出
def run_and_catch_all(c: callable):
    try:
        return c()
    except BaseException as e:
        # catch ALL exceptions, including KeyboardInterrupt and system exit
        print(type(e), e, sep=': ')


def try_invoke_function(f, name, is_method=False):
    print('[method]' if is_method else '[function]', name)

    def invoke():
        return invoke_function(f)

    ret = run_and_catch_all(invoke)

    if ret is not None:
        print('[return value]', repr(ret))
        return ret


def try_instantiate_class(c, name):
    print('[class]', name)

    def instantiate():
        return invoke_function(c)

    return run_and_catch_all(instantiate)


#尝试调用给定对象实例的方法should_investigate和mark_seen是可变的输入/输出变量，跟踪哪些类型被遍历TODO支持调用异步方法

def try_call_methods(instance, class_name, should_investigate, mark_seen):
    print('[instance methods]', class_name)

    def is_non_init_method(m):
        return inspect.ismethod(m) and m.__name__ != '__init__'

    for method_name, method in inspect.getmembers(instance, is_non_init_method):
        return_value = try_invoke_function(method, method_name, is_method=True)
        return_type = return_value.__class__
        # TODO should it be DFS or BFS?
        if should_investigate(return_type):
            print('[investigate type]', return_type)
            mark_seen(return_type)
            #try_call_methods(return_value, return_type, should_investigate, mark_seen)


PHASES = {
    'all': [install, import_package],
    'install': [install],
    'import': [import_package]
}


def main1():
    args = list(sys.argv)
    script = args.pop(0)

    if len(args) < 2 or len(args) > 4:
        raise ValueError(f'Usage: {script} [--local file | --version version] phase package_name')

    #手动解析参数以避免引入不必要的依赖关系和副作用
    local_path = None
    version = None
    package_name = None

    if args[0] == '--local':
        args.pop(0)
        local_path = args.pop(0)
    elif args[0] == '--version':
        args.pop(0)
        version = args.pop(0)

    phase = args.pop(0)

    if args:
        package_name = args.pop(0)

    if phase not in PHASES:
        print(f'Unknown phase {phase} specified.')
        exit(1)

    if package_name is None:
        # 单模块模式
        if phase == 'import' and local_path is not None:
            import_single_module(local_path)
            return
        else:
            print('install requested but no package name given, or local file missing for single module import')
            exit(1)

    package = Package(name=package_name, version=version, local_path=local_path)

    # Execute for the specified phase.
    for phase in PHASES[phase]:
        phase(package)


def dynamic_exec(name:Optional[str] = None,version:Optional[str] = None,local_path:Optional[str] = None):
    package = Package(name=name, version=version,local_path=local_path)
    #package = Package(name='requests', version='2.31.0', local_path='/Users/zhaozhouqiao/Desktop/poisoning_project/my_project/tmp/2023-09-19_19-14-43/requests')
    phase = 'all'
    # 执行特定的阶段
    for phase in PHASES[phase]:
        phase(package)
    return EXECUTION_LOG_PATH

