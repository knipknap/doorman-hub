// WARNING: This file is full of ugly hacks copied from the internet. Don't blame me.
function validate_email(email) {
  var email_re = /^([\w-\.]+@([\w-]+\.)+[\w-]{2,4})?$/;
  return email_re.test(email) && email.match(/(google|g)mail.\w+$/);
};

function infobox(msg) {
  $("#info").show('fast');
  $("#info").text(msg);
  $("#info").prop("class", "info");
};

function warnbox(msg) {
  $("#info").show('fast');
  $("#info").text(msg);
  $("#info").prop("class", "warning");
};

function errorbox(msg) {
  $("#info").show('fast');
  $("#info").text(msg);
  $("#info").prop("class", "error");
};

// I can't believe that neither JS nor jQuery provide a sane way for accessing
// query strings...
(function($) {
    $.QueryString = (function(a) {
        if (a == "") return {};
        var b = {};
        for (var i = 0; i < a.length; ++i) {
            var p = a[i].split('=');
            if (p.length != 2) continue;
                b[p[0]] = decodeURIComponent(p[1].replace(/\+/g, " "));
        }
        return b;
    })(window.location.search.substr(1).split('&'))
})(jQuery);

// Yeah, this hack is to fix val() for objects using add_bglabel below...
(function($){
  $.fn.oldval = $.fn.val;
  $.fn.val = function() {
    var res = $.fn.oldval.apply(this,arguments);
    if (this.hasClass('labeled-input'))
      return '';
    return res;
  };
})(jQuery);

function add_bglabel(input) {
    input.data('type', input.attr('type'));

    function notlabeled() {
        input.removeClass('labeled-input');
        input.attr('type', input.data('type'));
    };

    function labeled() {
        input.oldval(input.attr('title'));
        input.addClass('labeled-input');
        input.attr('type', 'text');
    };

    input.focus(function() {
        if(input.hasClass('labeled-input')) {
            input.oldval('');
            notlabeled();
        }
    });

    input.blur(function() {
        if(input.oldval() == '') {
            labeled();
        }
    });

    input.on('input', function() {
        notlabeled();
    });

    if(input.oldval() == '')
        labeled();
};
