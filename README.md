PHP_CodeSniffer Sublime Text 2/3 Plugin
========================================
PHP_CodeSniffer Sublime Text Plugin allows running of [PHP_CodeSniffer](https://github.com/squizlabs/PHP_CodeSniffer) inside Sublime Text.

Running the PHPCS command displays the coding standard violations report and displays gutter markers for the lines that have code violations.

Running the PHPCBF command attempts to fix the coding standard violations and displays a diff of the changes that were made.

Installation
--------------
- Clone [PHP_CodeSniffer](https://github.com/squizlabs/PHP_CodeSniffer) and switch to the **phpcs-fixer** branch.
- Install by cloning the plugin in to ST2/ST3 Packages directory.
```
git clone https://github.com/squizlabs/sublime-PHP_CodeSniffer PHP_CodeSniffer
```

Configuration
--------------
Configuration files can be opened via Preferences > Package Settings > PHP_CodeSniffer.

Make sure the php_path, phpcs_path and phpcbf_path paths are correct. E.g.
```
"phpcs_path": "/usr/local/bin/phpcs",
"phpcbf_path": "/usr/local/bin/phpcbf",
```


**phpcs_stantard**

This settings can be the name of a single standard or a list of folder/project names and the standard to be used for each project. E.g.
```
"phpcs_standard": "Squiz"
```
```
"phpcs_standard": {
    "PHP_CodeSniffer": "PHPCS",
    "php-sikuli": "PSR1",
    "Sublime-PHP_CodeSniffer": "PEAR"
}
```

**additional_args**

Array containing additional arguments to pass to the PHPCS/PHPCBF scripts.

**error_scope & warning_scope**

These settings define the colors used for the error and warning gutter markers.
```
// Gutter error icon color.
"error_scope": "comment.block",

// Gutter warning icon color.
"warning_scope": "function"
```

**run_on_save**

If set to *true* then buffer will be checked on each save.


Using
--------
There are two shortcuts that can be used for Sublime PHP_CodeSniffer plugin:
- **ALT + S**: Runs PHPCS command for the open buffer.
- **ALT + SHIFT + S**: Runs PHPCBF command for the open buffer.

These commands are also availble in Tools > PHP_CodeSniffer menu.