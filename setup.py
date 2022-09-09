from setuptools import setup, find_packages

setup(
    name='Kubernetes Deployment CLI',
    version='1.0',
    author="Philip Fischbacher",
    author_email="pfischbacher@gmail.com",
    description="""A Python command line tool that takes the Kubernetes
    version as an argument and deploys the corresponding version to the
    infracture.
    """,
    packages=find_packages(exclude=[
        'contrib',
        'docs',
        'tests*'
    ]),
    entry_points={
        'console_scripts': [
            'ck8s = ck8s.core:main'
        ],
    },
)
