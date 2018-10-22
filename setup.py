import sys

if sys.version_info < (3, 5):
    print("You need at least Python 3.5 for this application!")
    if sys.version_info[0] < 3:
        print("try running with python3 {}".format(" ".join(sys.argv)))
    sys.exit(1)

try:
    from setuptools import setup
except ImportError:
    print("Could not find setuptools")
    print("Try installing them with pip install setuptools")
    sys.exit(1)

setup(
    name='pyLMS7002Soapy',
    version='1.5.0',
    description='Python support for LMS7002M (SoapySDR backend)',
    url='https://github.com/psynosaur/pyLMS7002Soapy',
    author='Lime Microsystems - Psynosaur',
    packages=['pyLMS7002Soapy'],
    install_requires=['numpy',
                      'matplotlib',
                      'pyserial'
                      ]
)

