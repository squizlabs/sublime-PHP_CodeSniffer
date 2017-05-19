import os
import re
import sublime
import sublime_plugin
import subprocess
import string
import difflib
import threading

SETTINGS_FILE    = 'PHP_CodeSniffer.sublime-settings'
RESULT_VIEW_NAME = 'phpcs_result_view'

settings = sublime.load_settings(SETTINGS_FILE)

class PHP_CodeSniffer:
  # Type of the view, phpcs or phpcbf.
  file_view   = None
  view_type   = None
  window      = None
  processed   = False
  output_view = None
  process_anim_idx = 0
  process_anim = {
    'windows': ['|', '/', '-', '\\'],
    'linux': ['|', '/', '-', '\\'],
    'osx': [u'\u25d0', u'\u25d3', u'\u25d1', u'\u25d2']
  }

  def run(self, window, cmd, msg):
    self.window = window
    content = window.active_view().substr(sublime.Region(0, window.active_view().size()))

    tm = threading.Thread(target=self.loading_msg, args=([msg]))
    tm.start()

    t = threading.Thread(target=self.run_command, args=(self.get_command_args(cmd), cmd, content, window, window.active_view().file_name()))
    t.start()


  def loading_msg(self, msg):
    sublime.set_timeout(lambda: self.show_loading_msg(msg), 0)


  def process_phpcbf_results(self, fixed_content, window, content):
    # Remove the gutter markers.
    self.window    = window
    self.file_view = window.active_view()
    self.view_type = 'phpcbf'

    # Get the diff between content and the fixed content.
    difftxt = self.run_diff(window, content, fixed_content)
    self.processed = True

    if not difftxt:
      self.clear_view()
      return

    self.file_view.erase_regions('errors')
    self.file_view.erase_regions('warnings')

    # Store the current viewport position.
    scrollPos = self.file_view.viewport_position()

    # Show diff text in the results panel.
    self.show_results_view(window, difftxt)
    self.set_status_msg('');

    self.file_view.run_command('set_view_content', {'data':fixed_content, 'replace':True})

    # After the active view contents are changed set the scroll position back to previous position.
    self.file_view.set_viewport_position(scrollPos, False)


  def run_diff(self, window, origContent, fixed_content):
    try:
        a = origContent.splitlines()
        b = fixed_content.splitlines()
    except UnicodeDecodeError as e:
        sublime.status_message("Diff only works with UTF-8 files")
        return

    # Get the diff between original content and the fixed content.
    diff = difflib.unified_diff(a, b, 'Original', 'Fixed', lineterm='')
    difftxt = u"\n".join(line for line in diff)

    if difftxt == "":
      sublime.status_message('PHP_CodeSniffer did not make any changes')
      return

    difftxt = "\n PHP_CodeSniffer made the following fixes to this file:\n\n" + difftxt
    return difftxt


  def process_phpcs_results(self, data, window):
    self.processed = True
    self.window    = window
    self.file_view = window.active_view()
    self.view_type = 'phpcs'

    if data == '':
      self.file_view.erase_regions('errors')
      self.file_view.erase_regions('warnings')
      window.run_command("hide_panel", {"panel": "output." + RESULT_VIEW_NAME})
      self.set_status_msg('No errors or warnings detected.')
      return

    self.show_results_view(window, data)
    self.set_status_msg('');

    # Add gutter markers for each error.
    lines        = data.decode('utf-8').split("\n")
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
    window.active_view().add_regions('errors', err_regions, settings.get('error_scope'), 'Packages/PHP_CodeSniffer/icons/error.png', sublime.HIDDEN)
    window.active_view().add_regions('warnings', warn_regions, settings.get('warning_scope'), 'Packages/PHP_CodeSniffer/icons/warning.png', sublime.HIDDEN)

  def get_command_args(self, cmd_type):
    args = []

    if settings.get('php_path'):
      args.append(settings.get('php_path'))
    elif os.name == 'nt':
      args.append('php')

    if cmd_type == 'phpcs':
      args.append(settings.get('phpcs_path', 'phpcs'))
      args.append('--report=' + sublime.packages_path() + '/PHP_CodeSniffer/STPluginReport.php')
    else:
      args.append(settings.get('phpcbf_path', 'phpcbf'))

    standard_setting = settings.get('phpcs_standard')
    standard = ''

    if type(standard_setting) is dict:
      for folder in self.window.folders():
        folder_name = os.path.basename(folder)
        if folder_name in standard_setting:
          standard = standard_setting[folder_name]
          break

      if standard == '' and '_default' in standard_setting:
        standard = standard_setting['_default']
    else:
      standard = standard_setting

    if settings.get('phpcs_standard'):
      args.append('--standard=' + standard)

    args.append('-')

    if settings.get('additional_args'):
      args += settings.get('additional_args')

    return args

  def run_command(self, args, cmd, content, window, file_path):
    shell = False
    if os.name == 'nt':
      shell = True

    self.processed = False
    proc = subprocess.Popen(args, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)

    if file_path:
      phpcs_content = 'phpcs_input_file: ' + file_path + "\n" + content;
    else:
      phpcs_content = content;

    if proc.stdout:
      data = proc.communicate(phpcs_content.encode('utf-8'))[0]

    if cmd == 'phpcs':
      sublime.set_timeout(lambda: self.process_phpcs_results(data, window), 0)
    else:
      data = data.decode('utf-8')
      sublime.set_timeout(lambda: self.process_phpcbf_results(data, window, content), 0)

  def init_results_view(self, window):
    self.output_view = window.get_output_panel(RESULT_VIEW_NAME)
    self.output_view.set_syntax_file('Packages/Diff/Diff.tmLanguage')
    self.output_view.set_name(RESULT_VIEW_NAME)
    self.output_view.settings().set('gutter', False)

    self.clear_view()
    self.output_view.settings().set("file_path", window.active_view().file_name())
    return self.output_view

  def show_results_view(self, window, data):
    if sublime.version().startswith('2'):
      data = data.decode('utf-8').replace('\r', '')
    else:
      if type(data) is bytes:
        data = data.decode('utf-8').replace('\r', '')

    outputView = self.init_results_view(window)
    window.run_command("show_panel", {"panel": "output." + RESULT_VIEW_NAME})
    outputView.set_read_only(False)

    self.output_view.run_command('set_view_content', {'data':data})

    outputView.set_read_only(True)


  def set_status_msg(self, msg):
    sublime.status_message(msg)

  def show_loading_msg(self, msg):
    if self.processed == True:
      return

    msg = msg[:-2]
    msg = msg + ' ' + self.process_anim[sublime.platform()][self.process_anim_idx]

    self.process_anim_idx += 1;
    if self.process_anim_idx > (len(self.process_anim[sublime.platform()]) - 1):
      self.process_anim_idx = 0

    self.set_status_msg(msg)
    sublime.set_timeout(lambda: self.show_loading_msg(msg), 300)


  def clear_view(self):
    if self.output_view != None:
      self.output_view.set_read_only(False)
      self.output_view.run_command('set_view_content', {'data':''})
      self.output_view.set_read_only(True)

    self.file_view.erase_regions('errors')
    self.file_view.erase_regions('warnings')


  def line_clicked(self):
    if self.view_type == 'phpcs':
        self.handle_phpcs_line_click()
    else:
        self.handle_phpcbf_line_click()


  def handle_phpcs_line_click(self):
    region = self.output_view.line(self.output_view.sel()[0])
    line   = self.output_view.substr(region)

    if line.find('[ Click here to fix this file ]') != -1:
      self.run(self.window, 'phpcbf', 'Runnings PHPCS Fixer  ')
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



class set_view_content(sublime_plugin.TextCommand):
    def run(self, edit, data, replace=False):
      if replace == True:
        self.view.replace(edit, sublime.Region(0, self.view.size()), data)
      else:
        self.view.insert(edit, 0, data)


# Init PHPCS.
phpcs = PHP_CodeSniffer()

class PhpcbfCommand(sublime_plugin.WindowCommand):
  def run(self):
    phpcs.run(self.window, 'phpcbf', 'Runnings PHPCS Fixer  ')

class PhpcsCommand(sublime_plugin.WindowCommand):
  def run(self):
    phpcs.run(self.window, 'phpcs', 'Runnings PHPCS  ')


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

def plugin_loaded():
    global settings
    settings = sublime.load_settings(SETTINGS_FILE)
