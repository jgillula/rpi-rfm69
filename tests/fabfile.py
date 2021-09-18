#encoding:UTF-8
# pylint: disable=missing-docstring

# =============================================================================
# This fabfile will setup and run test on a remote Raspberry Pi
# =============================================================================

from os import environ
from fabric.api import cd, task, shell_env
from fabric.operations import run, prompt, sudo
from fabric.state import env
from fabric.contrib import files
from fabric.contrib.project import rsync_project
from fabtools.python import virtualenv, install_requirements
from termcolor import colored
from git import Repo

# =============================================================================
# SETTINGS
# =============================================================================

class Settings:
    DEPLOY_USER = "pi"                      # Username for access to pi
    ROOT_NAME = "rpi-rfm69-test"                # A system friendly name for test project
    DIR_PROJ = "/srv/" + ROOT_NAME + "/"    # The root
    DIR_ENVS = DIR_PROJ + 'envs/'           # Where the Virtual environment will live
    DIR_CODE = DIR_PROJ + 'code/'           # Where the code will live

    SYNC_DIRS = [
        ("../", DIR_CODE),
    ]
    # Requirements
    REQUIREMENTS_FILES = [
        DIR_CODE + 'tests/requirements_remote.txt',
    ]
    TEST_PYTHON_VERSIONS = [ (3,7) ] # pylint: disable=

# =============================================================================
# END OF SETTINGS
# =============================================================================

env.user = Settings.DEPLOY_USER

@task
def coverage():
    sync_files()
    run_coverage()

@task
def sync():
    sync_files()

@task
def test():
    sync_files()
    for version in Settings.TEST_PYTHON_VERSIONS:
        run_tests(version)

@task
def init():
    make_dirs()
    sync_files()
    set_permissions()
    for version in Settings.TEST_PYTHON_VERSIONS:
        create_virtualenv(version)
        install_venv_requirements(version)

# =============================================================================
# SUB TASKS
# =============================================================================

# ----------------------------------------------------------------------------------------
# Helper functions below
# ----------------------------------------------------------------------------------------

def print_title(title):
    pad = "-" * (80 - len(title) - 4)
    print(colored("-- {} {}".format(title, pad), 'blue', 'on_yellow'))

def print_test_title(title):
    pad = "-" * (80 - len(title) - 4)
    print(colored("-- {} {}".format(title, pad), 'white', 'on_blue'))

def print_error(message):
    print(colored(message, 'red'))

def print_success(message):
    print(colored(message, 'green'))

# ----------------------------------------------------------------------------------------
# Sub Tasks - Project
# ----------------------------------------------------------------------------------------

# Make project folders
def make_dirs():
    print_title('Making folders')
    for d in [Settings.DIR_PROJ, Settings.DIR_ENVS] + [y for x, y in Settings.SYNC_DIRS]:
        exists = files.exists(d)
        print("File", d, "exists?", exists)
        if not exists:
            sudo('mkdir -p {}'.format(d))
            sudo('chown -R %s %s' % (env.user, d))
    set_permissions()

# Sync project files to server
def sync_files():
    print_title('Synchronising code')
    for local_dir, remote_dir in Settings.SYNC_DIRS:
        print('Copy from {} to {}'.format(local_dir, remote_dir))
        rsync_project(
            remote_dir=remote_dir,
            local_dir=local_dir,
            exclude=("*.pyc", "*.db", "*.sqlite3", "*.log", "*.csv",
                     '__pycache__', '*.DS_Store', '*~', 'venv_*'),
            extra_opts="--filter 'protect *.csv' --filter 'protect *.json' --filter 'protect *.db' --exclude-from=../.gitignore",
            delete=False
        )

# Set folder permissions
def set_permissions():
    print_title('Setting folder and file permissions')
    sudo('chmod -R %s %s' % ("u=rwx,g=rwx,o=r", Settings.DIR_CODE))
    sudo('chmod -R %s %s' % ("u=rwx,g=rwx,o=r", Settings.DIR_ENVS))

def get_env(py_version):
    major, minor = py_version
    ver_name = "{}.{}".format(major, minor)
    env_name = "env-python-{}".format(ver_name)
    return Settings.DIR_ENVS + env_name, ver_name, env_name

# Create a new environments
def create_virtualenv(py_version):
    env_path, ver_name, _ = get_env(py_version)
    print_title('Creating Python {} virtual environment: {}'.format(py_version, env_path))
    sudo('pip3 install virtualenv')
    if files.exists(env_path):
        print("Virtual Environment already exists")
        return
    run('virtualenv -p python{0} {1}'.format(ver_name, env_path))

# Install Python requirments
def install_venv_requirements(py_version):
    env_path, _, _ = get_env(py_version)
    print_title('Installing remote virtual env requirements')
    with virtualenv(env_path):
        for path in Settings.REQUIREMENTS_FILES:
            if files.exists(path):
                install_requirements(path, use_sudo=False)
                print_success("Installed: {}".format(path))
            else:
                print_error("File missing: {}".format(path))
                return

def run_tests(py_version):
    env_path, _, _ = get_env(py_version)
    print_test_title('Running tests in venv: {}'.format(env_path))
    with virtualenv(env_path):
        with cd(Settings.DIR_CODE):
            run('coverage run --omit=RFM69/registers.py --branch --concurrency=thread --source=RFM69 -m pytest -x -rs tests/')

def run_coverage():
    repo = Repo("../.")

    uncommitted_files = []
    for diff in repo.head.commit.diff(None):
        file_path = diff.b_rawpath.decode("utf-8")
        if file_path.startswith("RFM69"):
            uncommitted_files.append(file_path)
    active_branch = repo.active_branch
    repo.remote().fetch()
    num_unpushed_commits = len(list(repo.iter_commits("{0}@{{u}}..{0}".format(active_branch))))
    num_unpulled_commits = len(list(repo.iter_commits("{0}..{0}@{{u}}".format(active_branch))))
    if uncommitted_files:
        print("There are uncommitted changes in your repository:")
        for file_path in uncommitted_files:
            print(file_path)
    if num_unpushed_commits > 0:
        print("Your branch is ahead of '{}/{}' by {} commit(s)".format(repo.remote().name, active_branch, num_unpushed_commits))
    if num_unpulled_commits > 0:
        print("Your branch is behind '{}/{}' by {} commit(s)".format(repo.remote().name, active_branch, num_unpulled_commits))
    if (uncommitted_files or
        num_unpushed_commits > 0 or
        num_unpulled_commits > 0):
        run_anyway = prompt("Continue running coverage anyway?", default="N")
        if run_anyway.lower() not in ["y", "yes"]:
            return

    py_version = Settings.TEST_PYTHON_VERSIONS[0]
    env_path, _, _ = get_env(py_version)
    print_test_title('Running coverage in venv: {}'.format(env_path))
    with virtualenv(env_path):
        with cd(Settings.DIR_CODE):
            repo_token = None
            need_to_rerun_tests = not files.exists(".coverage")
            if not need_to_rerun_tests:
                get_mtime_cmd = "date -r \"{}\" +%s"
                coverage_last_run_time = int(run(get_mtime_cmd.format(".coverage"), quiet=True))
                for filename in run("ls -1 tests/test_*.py", quiet=True).split() + run("ls -1 RFM69/*.py", quiet=True).split():
                    mtime = int(run(get_mtime_cmd.format(filename), quiet=True))
                    need_to_rerun_tests |= (mtime > coverage_last_run_time)
            if need_to_rerun_tests:
                print_title("Need to run tests to generate coverage file first")
                run_tests(py_version)
            if files.exists(".coverage"):
                run('coverage report')
                if "COVERALLS_REPO_TOKEN" not in environ:
                    repo_token = prompt("Enter your coveralls repo_token to upload the results (or just hit enter to cancel):")
                else:
                    repo_token = environ["COVERALLS_REPO_TOKEN"]
                if repo_token:
                    with shell_env(COVERALLS_REPO_TOKEN=repo_token):
                        run("coveralls")
