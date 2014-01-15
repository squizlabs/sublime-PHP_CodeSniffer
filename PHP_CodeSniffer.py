import os
import re
import sublime
import sublime_plugin
import subprocess
import StringIO
import difflib
import threading

RESULT_VIEW_NAME = 'phpcs_result_view'
settings         = sublime.load_settings('PHP_CodeSniffer.sublime-settings')

class PHP_CodeSniffer:
  # Type of the view, phpcs or phpcbf.
  file_view = None
  view_type = None
  window    = None

  def run(self, window, cmd):
    content = window.active_view().substr(sublime.Region(0, window.active_view().size()))
    t = threading.Thread(target=self.run_command, args=(self.get_command_args(cmd), cmd, content, window, window.active_view().file_name()))
    t.start()

  def process_phpcbf_results(self, newContent, window, content):
    # Get the diff between content and the new content.
    difftxt = self.runDiff(window, content, newContent)
    if not difftxt:
      self.clear_view()
      return

    # Remove the gutter markers.
    window.active_view().erase_regions('errors')
    window.active_view().erase_regions('warnings')
    self.window = window
    self.file_view = window.active_view()

    # Show results panel.
    outputView = self.initResultsPanel(window)
    self.showResultsPanel(window)
    self.view_type = 'phpcbf'

    # Replace the main view contents with the fixed content.
    scrollPos = window.active_view().viewport_position()
    mainEdit  = window.active_view().begin_edit()
    window.active_view().replace(mainEdit, sublime.Region(0, window.active_view().size()), newContent.decode('utf-8'))
    window.active_view().end_edit(mainEdit)

    # Print the diff in output view.
    outputView.set_read_only(False)
    edit = outputView.begin_edit()
    outputView.insert(edit, 0, difftxt)
    outputView.end_edit(edit)
    outputView.set_read_only(True)

    window.active_view().set_viewport_position(scrollPos, False)


  def runDiff(self, window, origContent, newContent):
    try:
        a = origContent.encode('utf-8').splitlines()
        b = newContent.splitlines()
    except UnicodeDecodeError as e:
        sublime.status_message("Diff only works with UTF-8 files")
        return

    # Get the diff between original content and the fixed content.
    diff = difflib.unified_diff(a, b, 'Original', 'Fixed', lineterm='')
    difftxt = u"\n".join(line.decode('utf-8') for line in diff)

    if difftxt == "":
      sublime.status_message('PHP_CodeSniffer did not make any changes')
      return

    difftxt = "\n PHP_CodeSniffer made the following fixes to this file:\n\n" + difftxt
    return difftxt


  def process_phpcs_results(self, data, window):
    if data == '':
      sublime.status_message('No errors or warnings detected.')
      return

    outputView = self.initResultsPanel(window)
    self.showResultsPanel(window)
    self.view_type = 'phpcs'
    self.window = window
    self.file_view = window.active_view()

    outputView.set_read_only(False)
    edit = outputView.begin_edit()
    outputView.insert(edit, outputView.size(), data)
    outputView.end_edit(edit)
    outputView.set_read_only(True)

    # Add gutter markers for each error.
    lines        = data.split("\n")
    err_regions  = []
    warn_regions = []
    col_regions  = []
    msg_type     = ''

    for line in lines:
      if line.find('Errors:') != -1:
        msg_type = 'error'
      elif line.find('Warnings:') != -1:
        msg_type = 'warning'
      else:
        match = re.match(r'[^:0-9]+([0-9]+)\s*:', line)
        if match:
          pt = window.active_view().text_point(int(match.group(1)) - 1, 0)
          if msg_type == 'error':
            err_regions.append(window.active_view().line(pt))
          else:
            warn_regions.append(window.active_view().line(pt))

    window.active_view().erase_regions('errors')
    window.active_view().erase_regions('warnings')
    window.active_view().add_regions('errors', err_regions, settings.get('error_scope'), '../PHP_CodeSniffer/icons/error', sublime.HIDDEN)
    window.active_view().add_regions('warnings', warn_regions, settings.get('warning_scope'), '../PHP_CodeSniffer/icons/warning', sublime.HIDDEN)

  def get_command_args(self, cmd_type):
    args = []

    if os.name == 'nt':
      args.append('start')
      args.append('/B')

    if settings.get('php_path'):
      args.append(settings.get('php_path'))
    elif os.name == 'nt':
      args.append('php')

    if cmd_type == 'phpcs':
      args.append(settings.get('phpcs_path', 'phpcs'))
      args.append('--report=' + sublime.packages_path() + '/PHP_CodeSniffer/STPluginReport.php')
    else:
      args.append(settings.get('phpcbf_path', 'phpcbf'))

    if settings.get('phpcs_standard'):
      args.append('--standard=' + settings.get('phpcs_standard'))

    if settings.get('additional_args'):
      args += settings.get('additional_args')

    return args

  def run_command(self, args, cmd, content, window, file_path):
    shell = False
    if os.name == 'nt':
      shell = True

    proc = subprocess.Popen(args, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)

    phpcsContent = 'phpcs_input_file: ' + file_path + "\n" + content;

    if proc.stdout:
      data = proc.communicate(phpcsContent.encode('utf-8'))[0]

    if cmd == 'phpcs':
      sublime.set_timeout(lambda: self.process_phpcs_results(data, window), 0)
    else:
      sublime.set_timeout(lambda: self.process_phpcbf_results(data, window, content), 0)

  def initResultsPanel(self, window):
    if not hasattr(self, 'output_view'):
      self.output_view = window.get_output_panel(RESULT_VIEW_NAME)
      self.output_view.set_syntax_file('Packages/Diff/Diff.tmLanguage')
      self.output_view.set_name(RESULT_VIEW_NAME)
      self.output_view.settings().set('gutter', False)

    self.clear_view()
    self.output_view.settings().set("file_path", window.active_view().file_name())
    return self.output_view


  def showResultsPanel(self, window):
    window.run_command("show_panel", {"panel": "output."+RESULT_VIEW_NAME})


  def clear_view(self):
    self.output_view.set_read_only(False)
    edit = self.output_view.begin_edit()
    self.output_view.erase(edit, sublime.Region(0, self.output_view.size()))
    self.output_view.end_edit(edit)
    self.output_view.set_read_only(True)


  def line_clicked(self):
    if self.view_type == 'phpcs':
        self.handle_phpcs_line_click()
    else:
        self.handle_phpcbf_line_click()


  def handle_phpcs_line_click(self):
    region = self.output_view.line(self.output_view.sel()[0])
    line   = self.output_view.substr(region)

    if line.find('[ Click here to fix this file ]') != -1:
      self.run(self.window, 'phpcbf')
      return
    else:
      match = re.match(r'[^:0-9]+([0-9]+)\s*:', line)
      if not match:
        return

    # Highlight the clicked results line.
    self.output_view.add_regions(RESULT_VIEW_NAME, [region], "comment", 'bookmark', sublime.DRAW_OUTLINED)

    lineNum = match.group(1)
    self.go_to_line(lineNum)


  def handle_phpcbf_line_click(self):
    pnt    = self.output_view.sel()[0]
    region = self.output_view.line(pnt)
    line   = self.output_view.substr(region)
    (row, col) = self.output_view.rowcol(pnt.begin())

    offset = 0
    found  = False
    while not found and row > 0:
      text_point = self.output_view.text_point(row, 0)
      line = self.output_view.substr(self.output_view.line(text_point))
      if line.startswith('@@'):
        match = re.match(r'^@@ -\d+,\d+ \+(\d+),.*', line)
        if match:
          lineNum = int(match.group(1)) + offset - 1
          self.go_to_line(lineNum)

        break
      elif not line.startswith('-'):
        offset = offset + 1

      row = row - 1


  def go_to_line(self, lineNum):
    self.window.focus_view(self.file_view)
    self.file_view.run_command("goto_line", {"line": lineNum})


# Init PHPCS.
phpcs = PHP_CodeSniffer()

class PhpcbfCommand(sublime_plugin.WindowCommand):
  def run(self):
    phpcs.run(self.window, 'phpcbf')

class PhpcsCommand(sublime_plugin.WindowCommand):
  def run(self):
    phpcs.run(self.window, 'phpcs')


class PhpcsEventListener(sublime_plugin.EventListener):
  def __init__(self):
    self.previous_region = None

  def on_query_context(self, view, key, operator, operand, match_all):
    # TODO: No idea if this is the right way but seems to work o.O
    if key == 'panel_visible':
      view.erase_regions('errors')
      view.erase_regions('warnings')

  def on_post_save(self, view):
    if settings.get('run_on_save', False) == False:
      return

    if view.file_name().endswith('.inc') == False:
      return

    sublime.active_window().run_command("phpcs")

  def on_selection_modified(self, view):
    if view.name() != RESULT_VIEW_NAME:
      return

    region = view.line(view.sel()[0])

    if self.previous_region == region:
      return

    self.previous_region = region
    phpcs.line_clicked()