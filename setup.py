# from distribute_setup import use_setuptools
# use_setuptools() 

from setuptools import setup, find_packages
from requirements_utils import parse_dependency_links, parse_requirements

print find_packages()
setup(
    name='jinja2js',
    version='0.1.0-pre-alpha',
    url='https://github.com/syrusakbary/jinja2js',
    download_url = 'git@github.com:syrusakbary/jinja2js.git',
    author='Syrus Akbary',
    author_email='me@syrusakbary.com',
    description='Jinja2 to javascript compiler',
    # long_description=open('README').read(),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Scientific/Engineering',
    ],
    platforms='any',
    packages=find_packages(),
    keywords='jinja2 javascript converter',
    include_package_data=True,
    entry_points={
        'console_scripts' : ['jinja2js = jinja2js.generate:generate_template',]
    },
    install_requires = parse_requirements('requirements.txt'),
    dependency_links = parse_dependency_links('requirements.txt'),
    setup_requires = ['nose>=1.0'],
    tests_require = parse_requirements('requirements-test.txt'),
    # test_dirs='jinja2js/testsuite',
    test_suite = "nose.collector"
)
