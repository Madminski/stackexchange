import sys
from importlib.metadata import distribution
import configparser

REQUIRED_PYTHON = "python3"
CONFIG_FILE = 'config.ini'
REQUIRED_CONFIG_VARS = [
    ('logging', 'log_level'),
    ('logging', 'log_directory'),
    ('logging', 'log_filename'),
    ('make_dataset', 'input_file'),
    ('make_dataset', 'output_dir'),
    ('make_dataset', 'data_dir'),
    ('make_dataset', 'project_dir'),
    ('make_dataset', 'chunk_size')
]


def check_python_version():
    system_major = sys.version_info.major
    if REQUIRED_PYTHON == "python":
        required_major = 2
    elif REQUIRED_PYTHON == "python3":
        required_major = 3
    else:
        raise ValueError("Unrecognized python interpreter: {}".format(
            REQUIRED_PYTHON))

    if system_major != required_major:
        raise TypeError(
            "This project requires Python {}. Found: Python {}".format(
                required_major, sys.version))
    else:
        print(">>> Correct Python version found!")


def check_packages():
    with open('requirements.txt', 'r') as f:
        requirements = f.read().splitlines()
    for requirement in requirements:
        if not requirement or requirement.startswith('#') or requirement.startswith('-e'):
            continue
        package = requirement.split('==')[0]
        try:
            distribution(package)
            print(f">>> {package} is installed")
        except Exception:
            print(f">>> {package} is NOT installed")


def check_config_file():
    config = configparser.ConfigParser()
    if not config.read(CONFIG_FILE):
        print(f"{CONFIG_FILE} is NOT found - Please modify from template_config.ini")
        return
    for section, var in REQUIRED_CONFIG_VARS:
        try:
            value = config.get(section, var)
            print(f"{section}.{var} is set to {value}")
        except (configparser.NoSectionError, configparser.NoOptionError):
            print(f">>> {section}.{var} is NOT set")


def main():
    check_python_version()
    check_packages()
    check_config_file()


if __name__ == '__main__':
    main()
