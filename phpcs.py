import os
import sublime
import sublime_plugin
import subprocess
import StringIO
import difflib

RESULT_VIEW_NAME = 'phpcs_result_view'
settings         = sublime.load_settings('sublime-phpcs.sublime-settings')

phpcs = PHPCS()

class PHPCS:
  def runPhpcbf(self, window, content=''):
    if not content:
      content = window.active_view().substr(sublime.Region(0, window.active_view().size()))

    args = [settings.get('phpcbf_path', 'phpcbf')]

    if settings.get('phpcs_standard'):
      args.append('--standard=' + settings.get('phpcs_standard'))

    proc = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    if proc.stdout:
      newContent = proc.communicate(content)[0]

    self.runDiff(window, content, newContent)

  def runDiff(self, window, origContent, newContent):
    try:
        a = origContent.splitlines()
        b = newContent.splitlines()
    except UnicodeDecodeError:
        sublime.status_message("Diff only works with UTF-8 files")
        return

    diff = difflib.unified_diff(a, b, lineterm='')
    difftxt = u"\n".join(line for line in diff)

    if difftxt == "":
        sublime.status_message("No changes")
        return

    window.active_view().erase_regions('errors')
    window.active_view().erase_regions('warnings')

    mainEdit = window.active_view().begin_edit()
    window.active_view().replace(mainEdit, sublime.Region(0, window.active_view().size()), newContent)
    window.active_view().end_edit(mainEdit)

    v = window.get_output_panel('unsaved_changes')
    v.set_syntax_file('Packages/Diff/Diff.tmLanguage')
    v.settings().set('word_wrap', window.active_view().settings().get('word_wrap'))

    edit = v.begin_edit()
    v.insert(edit, 0, difftxt)
    v.end_edit(edit)

    window.run_command("show_panel", {"panel": "output.unsaved_changes"})


  def runPhpcs(self, window, outputView, content):
    # PHPCS cmd args.
    args = [settings.get('phpcs_path', 'phpcs')]

    if settings.get('phpcs_standard'):
      args.append('--standard=' + settings.get('phpcs_standard'))

    args.append('--report-width=300')

    proc = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    if proc.stdout:
      data = proc.communicate(content)[0]

    data = data.replace('PHPCBF CAN FIX', 'CLICK HERE TO FIX')

    outputView.set_read_only(False)
    outputView.set_syntax_file('Packages/Diff/Diff.tmLanguage')
    edit = outputView.begin_edit()
    outputView.insert(edit, outputView.size(), data)
    outputView.end_edit(edit)
    outputView.set_read_only(True)

    # Add gutter markers for each error.
    lines        = data.split("\n")
    err_regions  = []
    warn_regions = []
    col_regions  = []
    for line in lines:
      lparts = line.split("|")
      if len(lparts) == 3:
        line = int(lparts[0])
        pt = window.active_view().text_point(line - 1, 0)
        #startCol = pt
        #endCol   = startCol + 10
        #col_regions.append(sublime.Region(startCol, endCol))
        if lparts[1].strip() == 'ERROR':
          err_regions.append(window.active_view().line(pt))
        else:
          warn_regions.append(window.active_view().line(pt))

    window.active_view().erase_regions('errors')
    window.active_view().erase_regions('warnings')
    window.active_view().add_regions('errors', err_regions, settings.get('error_scope'), '../Phpcs/icons/error', sublime.HIDDEN)
    window.active_view().add_regions('warnings', warn_regions, settings.get('warning_scope'), '../Phpcs/icons/warning', sublime.HIDDEN)
    #window.active_view().add_regions('col_reg', col_regions, settings.get('warning_scope'), '../Phpcs/icons/warning')


class ShowPhpcsResultCommand(sublime_plugin.WindowCommand):
  def run(self):
    self.window.run_command("show_panel", {"panel": "output." + RESULT_VIEW_NAME})

class PhpcbfCommand(sublime_plugin.WindowCommand):
  def run(self):
    phpcs.runPhpcbf(self.window)

class PhpcsCommand(sublime_plugin.WindowCommand):
  def run(self):
    file_path = self.window.active_view().file_name()
    file_name = os.path.basename(file_path)

    self.file_path = file_path
    self.file_name = file_name
    self.resultsPanelVisible = False

    self.initResultsPanel()
    self.showResultsPanel()

    content = self.window.active_view().substr(sublime.Region(0, self.window.active_view().size()))
    phpcs.runPhpcs(self.window, self.output_view, content)


  def initResultsPanel(self):
    if not hasattr(self, 'output_view'):
      self.output_view = self.window.get_output_panel(RESULT_VIEW_NAME)
      self.output_view.set_name(RESULT_VIEW_NAME)
    self.clear_view()
    self.output_view.settings().set("file_path", self.file_path)

  def showResultsPanel(self):
    if self.resultsPanelVisible:
      return
    self.window.run_command("show_panel", {"panel": "output."+RESULT_VIEW_NAME})
    self.resultsPanelVisible = True

  def clear_view(self):
    self.output_view.set_read_only(False)
    edit = self.output_view.begin_edit()
    self.output_view.erase(edit, sublime.Region(0, self.output_view.size()))
    self.output_view.end_edit(edit)
    self.output_view.set_read_only(True)

class PhpcsEventListener(sublime_plugin.EventListener):
  def __init__(self):
    self.previous_region = None
    self.file_view = None

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
    window = sublime.active_window()

    text = view.substr(region).split('|')
    if len(text) != 3:
      if text[0].startswith('CLICK HERE'):
        phpcs.runPhpcbf(window)
      return

    # Highlight the clicked results line.
    view.add_regions(RESULT_VIEW_NAME, [region], "string", '', sublime.DRAW_OUTLINED)

    # Find the file view.
    file_view = self.file_view
    if not file_view:
      file_path = view.settings().get('file_path')
      file_view = None
      for v in window.views():
        if v.file_name() == file_path:
          file_view = v
          break

      if file_view == None:
        return

      self.file_view = file_view

    lineNum = int(text[0])
    window.focus_view(file_view)
    file_view.run_command("goto_line", {"line": lineNum})
    file_region = file_view.line(file_view.sel()[0])