<?php
/**
 * Sublime Text Plugin report for PHP_CodeSniffer.
 *
 * @author    Greg Sherwood <gsherwood@squiz.net>
 * @copyright 2006-2015 Squiz Pty Ltd (ABN 77 084 670 600)
 * @license   https://github.com/squizlabs/PHP_CodeSniffer/blob/master/licence.txt BSD Licence
 */

namespace PHP_CodeSniffer_SublimePlugin;

use PHP_CodeSniffer\Files\File;
use PHP_CodeSniffer\Reports\Report;

class STPluginReport implements Report
{


    /**
     * Generate a partial report for a single processed file.
     *
     * Function should return TRUE if it printed or stored data about the file
     * and FALSE if it ignored the file. Returning TRUE indicates that the file and
     * its data should be counted in the grand totals.
     *
     * @param array                $report      Prepared report data.
     * @param PHP_CodeSniffer_File $phpcsFile   The file being reported on.
     * @param boolean              $showSources Show sources?
     * @param int                  $width       Maximum allowed line width.
     *
     * @return boolean
     */
    public function generateFileReport($report, File $phpcsFile, $showSources=false, $width=80)
    {
        if ($report['errors'] === 0 && $report['warnings'] === 0) {
            // Nothing to print.
            return false;
        }

        echo PHP_EOL;
        echo ' PHP_CodeSniffer found '.$report['errors'].' error';
        if ($report['errors'] !== 1) {
            echo 's';
        }

        if ($report['warnings'] > 0) {
            echo ' and '.$report['warnings'].' warning';
            if ($report['warnings'] !== 1) {
                echo 's';
            }
        }

        echo ' affecting '.count($report['messages']).' line';
        if (count($report['messages']) !== 1) {
            echo 's';
        }

        echo PHP_EOL;

        // Print the fixable message.
        if ($report['fixable'] > 0) {
            echo PHP_EOL;
            $message = 'Good news! ';
            if ($report['fixable'] > 1) {
                $message .= 'The '.$report['fixable'].' marked sniff violations';
            } else {
                $message .= 'The marked sniff violation';
            }

            $message .= ' below can be fixed automatically';

            $length = (strlen($message) + 4);

            $fixButton    = '[ Click here to fix this file ]';
            $leftPadding  = floor(($length - 4 - strlen($fixButton)) / 2);
            $rightPadding = ($length - $leftPadding - strlen($fixButton) - 4);
            $fixMessage   = str_repeat(' ', $leftPadding).$fixButton.str_repeat(' ', $rightPadding);

            echo ' '.str_repeat('-', $length).PHP_EOL;
            echo ' | '.$message.' |'.PHP_EOL;
            echo ' | '.$fixMessage.' |'.PHP_EOL;
            echo ' '.str_repeat('-', $length).PHP_EOL;
        }//end if

        echo PHP_EOL.' Note: click a sniff violation below to jump directly to the relevant line'.PHP_EOL;

        // Work out the max line number for formatting.
        $maxLine = 0;
        foreach ($report['messages'] as $line => $lineErrors) {
            if ($line > $maxLine) {
                $maxLine = $line;
            }
        }

        $maxLineLength = strlen($maxLine);

        if ($report['errors'] > 0) {
            echo PHP_EOL.' Errors:'.PHP_EOL;
            foreach ($report['messages'] as $line => $lineErrors) {
                foreach ($lineErrors as $column => $colErrors) {
                    foreach ($colErrors as $error) {
                        if ($error['type'] !== 'ERROR') {
                            continue;
                        }

                        $message = $error['message'];
                        if ($showSources === true) {
                            $message .= ' ('.$error['source'].')';
                        }

                        echo ' ';
                        if ($report['fixable'] > 0) {
                            echo '[';
                            if ($error['fixable'] === true) {
                                echo 'x';
                            } else {
                                echo ' ';
                            }

                            echo '] ';
                        }

                        $padding  = ($maxLineLength - strlen($line));
                        echo 'Line '.$line.str_repeat(' ', $padding).': '.$message.PHP_EOL;
                    }//end foreach
                }//end foreach
            }//end foreach
        }//end if

        if ($report['warnings'] > 0) {
            echo PHP_EOL.' Warnings:'.PHP_EOL;
            foreach ($report['messages'] as $line => $lineErrors) {
                foreach ($lineErrors as $column => $colErrors) {
                    foreach ($colErrors as $error) {
                        if ($error['type'] !== 'WARNING') {
                            continue;
                        }

                        $message = $error['message'];
                        if ($showSources === true) {
                            $message .= ' ('.$error['source'].')';
                        }

                        echo ' ';
                        if ($report['fixable'] > 0) {
                            echo '[';
                            if ($error['fixable'] === true) {
                                echo 'x';
                            } else {
                                echo ' ';
                            }

                            echo '] ';
                        }

                        $padding  = ($maxLineLength - strlen($line));
                        echo 'Line '.$line.str_repeat(' ', $padding).': '.$message.PHP_EOL;
                    }//end foreach
                }//end foreach
            }//end foreach
        }//end if

        return true;

    }//end generateFileReport()


    /**
     * Prints all errors and warnings for each file processed.
     *
     * @param string  $cachedData    Any partial report data that was returned from
     *                               generateFileReport during the run.
     * @param int     $totalFiles    Total number of files processed during the run.
     * @param int     $totalErrors   Total number of errors found during the run.
     * @param int     $totalWarnings Total number of warnings found during the run.
     * @param int     $totalFixable  Total number of problems that can be fixed.
     * @param boolean $showSources   Show sources?
     * @param int     $width         Maximum allowed line width.
     * @param boolean $toScreen      Is the report being printed to screen?
     *
     * @return void
     */
    public function generate(
        $cachedData,
        $totalFiles,
        $totalErrors,
        $totalWarnings,
        $totalFixable,
        $showSources=false,
        $width=80,
        $toScreen=true
    ) {
        echo $cachedData;

    }//end generate()


}//end class

?>
