(function() {
    var clock = null,
        h_hours = null,
        h_minutes = null,
        h_seconds = null;
        
    var set_css_rotation = function(element, rotation) {
        if ((element != null) && (isNaN(rotation) == false)) {
            var value = 'rotate(' + rotation + 'deg)';
            element.setStyles({
                '-webkit-transform': value,
                '-moz-transform': value,
                'transform': value
            });
        }
    };
        
    var update_hands = function() {
        var current_date = new Date();
        set_css_rotation(h_seconds, current_date.getSeconds() * 6);
        set_css_rotation(h_minutes, current_date.getMinutes() * 6);
        
        var hours = current_date.getHours();
        if (hours >= 12) {
            hours -= 12;
        }
        set_css_rotation(h_hours, hours * 30);
    };
    
    window.addEvent('domready', function() {
        clock = $('clock');
        h_hours = clock.getElement('div.hand.hours');
        h_minutes = clock.getElement('div.hand.minutes');
        h_seconds = clock.getElement('div.hand.seconds');
        update_hands();
        var interval = window.setInterval(update_hands, 1000);
    });
})();