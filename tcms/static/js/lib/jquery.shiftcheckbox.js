/**
 * JQuery shiftcheckbox plugin
 *
 * shiftcheckbox provides a simpler and faster way to select/unselect multiple checkboxes within a given range with just two clicks.
 * Inspired from GMail checkbox functionality
 *
 * Just call $('.<class-name>').shiftcheckbox() in $(document).ready
 *
 * @name shiftcheckbox
 * @type jquery
 * @cat Plugin/Form
 * @return JQuery
 *
 * This plugin is mostly based on the work done by <adityamooley@sanisoft.com>.
 * Changes are made by <cbtchn@gmail.com> by replacing the $.bind with $.live in
 * order to support future binding, as well as the bug fix caused by this change.
 */

(function ($) {
  $.fn.shiftcheckbox = function() {

    var prevChecked = null;
    var selectorStr = this.selector;

    function handleClick(event){
      var val = this.value;
      var checkStatus = this.checked;
      //get the checkbox number which the user has checked

      //check whether user has pressed shift
      if (event.shiftKey) {
        if (prevChecked != 'null') {
          //get the current checkbox number
          var ind = 0, found = 0, currentChecked;
          currentChecked = getSelected(val);

          ind = 0;
          if (currentChecked < prevChecked) {
            $(selectorStr).each(function(i) {
              if (ind >= currentChecked && ind <= prevChecked) {
                // I don't know why I had to manually trigger 'change' event.
                // Maybe this plugin is drunk, or I am.
                $(this).attr('checked', checkStatus).trigger('change');
              }
              ind++;
            });
          } else {
            $(selectorStr).each(function(i) {
              if (ind >= prevChecked && ind <= currentChecked) {
                $(this).attr('checked', checkStatus).trigger('change');
              }
              ind++;
            });
          }

          prevChecked = currentChecked;
        }
      } else {
        if (checkStatus) {
          prevChecked = getSelected(val);
        }
      }

    };

    function getSelected(val) {
      var ind = 0, found = 0, checkedIndex;
      $(selectorStr).each(function(i) {
        if (val == this.value && found != 1) {
          checkedIndex = ind;
          found = 1;
        }
        ind++;
      });
      return checkedIndex;
    };

    $(selectorStr).live("click", handleClick);
  };
})(jQuery);