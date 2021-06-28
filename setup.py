from setuptools import setup

requires = [
    'flask',
    'pyserial',
    'playsound'
]

setup(name='papaguy-tamer',
      version='0.1',
      description='communicate with papaguy',
      url='http://github.com/qm210/papaguy-tamer',
      author='qm210',
      author_email='quantemace@gmail.com',
      packages=['papaguy-tamer'],
      install_requires = requires
)

# FLASK_APP, DEBUG = ...?