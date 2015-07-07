PHP_CodeSniffer Sublime Text 2/3 Plugin
========================================
PHP_CodeSniffer Sublime Text Plugin allows running of [PHP_CodeSniffer](https://github.com/squizlabs/PHP_CodeSniffer) inside Sublime Text.

Running the PHPCS command displays the coding standard violations report and displays gutter markers for the lines that have code violations.

<a href="http://squizlabs.github.io/sublime-PHP_CodeSniffer/sublime-phpcs.png" target="_blank"><img src="http://squizlabs.github.io/sublime-PHP_CodeSniffer/sublime-phpcs-sm.png" alt="PHPCS screenshot" /></a>

Running the PHPCBF command attempts to fix the coding standard violations and displays a diff of the changes that were made.

<a href="http://squizlabs.github.io/sublime-PHP_CodeSniffer/sublime-phpcbf.png" target="_blank"><img src="http://squizlabs.github.io/sublime-PHP_CodeSniffer/sublime-phpcbf-sm.png" alt="PHPCS Fixer screenshot" /></a>



Installation
--------------
- Install [PHP_CodeSniffer](https://github.com/squizlabs/PHP_CodeSniffer).
- Clone the PHP_CodeSniffer Sublime Text Plugin in to ST2/ST3 Packages directory.
```
git clone https://github.com/squizlabs/sublime-PHP_CodeSniffer PHP_CodeSniffer
```
- Packages directory locations:
```
Mac: /Users/{user}/Library/Application Support/Sublime Text 2/Packages
Windows: C:\Users\{user}\AppData\Roaming\Sublime Text 2\Packages
Linux: ~/.config/sublime-text-2/Packages
```

Configuration
--------------
Configuration files can be opened via Preferences > Package Settings > PHP_CodeSniffer.

Make sure the php_path, phpcs_path and phpcbf_path paths are correct. E.g.
```
"phpcs_path": "/usr/local/bin/phpcs",
"phpcbf_path": "/usr/local/bin/phpcbf",
```


**phpcs_standard**

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


Usage
--------
There are two shortcuts that can be used for Sublime PHP_CodeSniffer plugin:
- **ALT + S**: Runs PHPCS command for the open buffer.
- **ALT + SHIFT + S**: Runs PHPCBF command for the open buffer.

These commands are also available in Tools > PHP_CodeSniffer menu.
