.. _Contribute:

Contribute
==========
`Feeds uses GitHub`_ as development platform.

Issues
~~~~~~
* Search the existing issues in the `issue tracker`_.
* File a `new issue`_ in case the issue is undocumented.

Pull requests
~~~~~~~~~~~~~
* Fork the project to your private repository.
* Create a topic branch and make your desired changes.
* Open a pull request. Make sure the GitHub CI checks are passing.

Create a new release
~~~~~~~~~~~~~~~~~~~~
* Cleanup: ``python setup.py clean --all ; rm -rf dist``
* Install dependencies: ``pip install twine wheel``
* Run: ``./scripts/new-release``
* Commit, tag and push both
* Build: ``python setup.py sdist bdist_wheel``
* Upload to TestPyPI: ``twine upload -r testpypi dist/*``
* Check upload on TestPyPI
* Upload to PyPi: ``twine upload dist/*``
* Upload a new Docker image

.. _Feeds uses GitHub: https://github.com/pyfeeds/pyfeeds
.. _issue tracker: https://github.com/pyfeeds/pyfeeds/issues
.. _new issue: https://github.com/pyfeeds/pyfeeds/issues/new
