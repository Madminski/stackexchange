from setuptools import find_packages, setup

setup(
    name='src',
    packages=find_packages(),
    version='0.1.0',
    description='The Stack Exchange Analysis Project is an attempt to uncover potential insights into the software '
                'community by examining trends, popular topics, and user interactions on the platform. Inspired by my '
                'experience as a Technical Service Manager, the goal of this project is to simulate the challenges of '
                'gathering and presenting useful intelligence from a massive data set. '
                'We\'ll start our project from scratch, creating a Conda environment in PyCharm, utilizing the Windows '
                'Subsystem for Linux (WSL) with Ubuntu, and employing the Cookiecutter Data Science template. Our '
                'ultimate goal is to develop an NLP/BI dashboard that might help us visualize and comprehend the data'
                ' more effectively.',
    author='Mark Curtis',
    license='BSD-3',
)
