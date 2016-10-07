/**
 * Logic for Website Edit Mode
 *
 */

// Register module
Website.modules.define("websiteEditMode", function () {

  var self = this;

  self.showContent = function () {
    var $contentWrapper = $(this),
        $contentInfo, width, height;
    $contentInfo = $contentWrapper.find('.cms-content-info');
    width = $contentWrapper.width();
    height = $contentWrapper.height();
    if (width < 300) {
      width = 300;
    }
    if (height < 60) {
      height = 60;
    }
    $contentInfo.css({width: width, height: height}).show();
  };

  self.hideContent = function () {
    var $contentWrapper = $(this);
    $contentWrapper.find('.cms-content-info').hide();
  };

  Website.events.bind('website:ready', function () {
    var $contentWrappers = $('.cms-content-wrapper');
    $contentWrappers.mouseenter(self.showContent);
    $contentWrappers.mouseleave(self.hideContent);
  });

});