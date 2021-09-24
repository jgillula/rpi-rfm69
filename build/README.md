# How to Build for Release on PyPi

Part of these instructions are cribbed from [https://packaging.python.org/tutorials/packaging-projects/](https://packaging.python.org/tutorials/packaging-projects/), and are meant for a Linux OS. They assume you've already set up an account and [gotten an API token on pypi.org](https://pypi.org/manage/account/#api-tokens).

1. Create a branch named with the new version number, if you haven't already
1. Ensure that the version number is set in [```../VERSION```](../VERSION)
1. Make sure to update [```../CHANGELOG.md```](../CHANGELOG.md)
1. Update the documentation as necessary
1. Make sure all the tests pass per the instructions at [```../tests/readme.md```](../tests/readme.md)
1. Push the branch to Github with ```git push --set-upstream origin VERSION``` where ```VERSION``` is the version number/name of the branch
1. Make sure the documentation for that version builds at [https://readthedocs.org/projects/rpi-rfm69/builds/](https://readthedocs.org/projects/rpi-rfm69/builds/)
1. Create a pull request, and then merge the version branch into main
1. Delete the version branch on Github
1. Checkout main
1. Do ```source build.sh``` in this directory to create a virtual environment and build the release files
1. Upload the new packages to pypi by doing ```python3 -m twine upload -u __token__ dist/*``` and entering your API token
1. Create a new tag for the release, using the contents of [```../CHANGELOG.md```](../CHANGELOG.md) as the description of the release, and uploading the files from ```dist``` as the binaries
1. Make sure the documentation for the latest release builds again at [https://readthedocs.org/projects/rpi-rfm69/builds/](https://readthedocs.org/projects/rpi-rfm69/builds/)

To clean up the build, just do ```source clean.sh```.
