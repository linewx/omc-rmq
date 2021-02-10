from setuptools import setup, find_packages
install_requires = [
    'requests==2.22.0',
    'dynaconf[all]==2.2.3',
    'pyfiglet==0.8.post1',
    'Click==7.0',
    'psutil',
    'kubernetes==11.0.0',
    'ruamel.yaml==0.16.12',
    'prettytable==0.7.2'
]


setup(
    name='omc-rmq',
    version="0.1.5",
    description=' command',
    license='MIT',
    author='Lu Ganlin',
    author_email='linewx1981@gmail.com',
    url='https://github.com/linewx/omc',
    packages=find_packages(),
    # package_data={'omc.config': ['*.yaml'], 'omc.lib': ['**', '**/*', '**/**/*']},
    install_requires=install_requires,
   
)
