import os
import subprocess
import json


def _invoke_semgrep(target, rules):
    exclude = [
        "helm",
        ".idea",
        "venv",
        "test",
        "tests",
        ".env",
        "dist",
        "build",
        "semgrep",
        "migrations",
        ".github",
        ".semgrep_logs",
    ]
    try:
        cmd = ["semgrep"]
        for rule in rules:
            cmd.extend(["--config", rule])
        for excluded in exclude:
            cmd.append(f"--exclude='{excluded}'")
        cmd.append("--no-git-ignore")
        cmd.append("--json")
        cmd.append("--quiet")
        cmd.append(target)
        result = subprocess.run(cmd, capture_output=True, check=True, encoding="utf-8")
        return json.loads(str(result.stdout))
    except FileNotFoundError:
        raise Exception("unable to find semgrep binary")
    except subprocess.CalledProcessError as e:
        error_message = f"""
        An error occurred when running Semgrep.
        command: {" ".join(e.cmd)}
        status code: {e.returncode}
        output: {e.output}
        """
        raise Exception(error_message)
    except json.JSONDecodeError as e:
        raise Exception("unable to parse semgrep JSON output: " + str(e))


def _format_semgrep_response(response, rule=None, targetpath=None):
    results = {}
    issues = 0
    for result in response["results"]:
        rule_name = rule or result["check_id"].split(".")[-1]
        code_snippet = result["extra"]["lines"]
        line = result["start"]["line"]

        file_path = os.path.abspath(result["path"])
        if targetpath:
            file_path = os.path.relpath(file_path, targetpath)

        location = file_path + ":" + str(line)
        code = trim_code_snippet(code_snippet)
        if rule_name not in results:
            issues += 1
            results[rule_name] = []
            results[rule_name].append({
                'location': location,
                'code': code,
                'message': result["extra"]["message"]
            })
        else:
            issues += 1
            results[rule_name].append({
                'location': location,
                'code': code,
                'message': result["extra"]["message"]
            })
    return issues,results


def trim_code_snippet(code):
    THRESHOLD = 250
    if len(code) > THRESHOLD:
        return code[: THRESHOLD - 10] + '...' + code[len(code) - 10:]
    else:
        return code


def static_analyse(path_to_detect):
    rules_name = os.listdir("./static_rules/")
    current_file_path = os.path.abspath(__file__)  # 获取当前文件的绝对路径
    current_file_dir = os.path.dirname(current_file_path)
    rules_path = [current_file_dir + '/static_rules/' + x for x in rules_name]
    try:
        #results_empty = {rule[:-4]: [] for rule in rules_name}
        response = _invoke_semgrep(path_to_detect, rules_path)
        issues,results = _format_semgrep_response(response)
        #issues = len(results)
        #results = results | results_empty
        return issues, results
    except Exception as e:
        print("semgrep出问题")


#print(static_analyse("/Users/zhaozhouqiao/Downloads/pypi_malregistry-main/baeutifulsoup"))
