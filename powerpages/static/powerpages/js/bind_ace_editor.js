/**
 * Converts particular textareas into Ace editor instances.
 */
(function($){

  $(document).ready(function(){
    $('.handle-ace-editor').each(function(index, item){
      var $textarea, name, width, height, containerID, $container, editor,
          theme, mode;
      // Prepare container, hide text area
      $textarea = $(item);
      name = $textarea.attr('name');
      width = $textarea.data('ace-width') || 960;
      height = $textarea.data('ace-height');
      if (!height){
        height = $textarea.val().split('\n').length * 13 + 20;
        if (height < 300){
          height = 300;
        }
      }
      containerID = 'ace-editor-' + name;
      $container = $('<div id="' + containerID + '" data-ace-for="' + name + '">');
      $container.css({width: width, height: height});
      $textarea.hide().after($container);
      // Create and configure editor instance
      editor = ace.edit(containerID);
      theme = $textarea.data('ace-theme') || "ace/theme/monokai";
      editor.setTheme(theme);
      mode = $textarea.data('ace-mode') || "ace/mode/django";
      editor.getSession().setMode(mode);
      $textarea.data('ace-instance', editor);
      // Set text inside of editor and connect change event handler:
      editor.getSession().setValue($textarea.val());
      editor.getSession().on('change', function(){
        $textarea.val(editor.getSession().getValue());
      });
    });
  });

})(jQuery || django.jQuery);
