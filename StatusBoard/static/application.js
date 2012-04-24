(function() {
    var people = null;
    var projects_scroll_timeout = null;
    
    var ajax_error = function() {
        alert('Communication error');
    };
    
    var load_people = function(callback) {
        callback = callback || function() {};
        var request = new Request.JSON({
            'url': '/people',
            'method': 'GET',
            'onFailure': ajax_error,
            'onSuccess': function(data) {
                people = data;
                callback();
            }
        }).send();
    };
    
    var gravatar_url = function(mail_hash, size) {
        size = size || 60;
        
        return 'http://gravatar.com/avatar/' + mail_hash + '?s=' + size;
    };
    
    var xmpp_queue = (function() {
        var queue = [];
        var timeout = null;
        var current_index = 0;
        
        var next_message = function() {
            var message = queue[current_index];
            if (message === undefined) {
                return;
            }
            
            var show_new_msg = function() {
                var new_msg = new Element('p', {
                    'id': 'msg',
                    'html': '<img width="76" height="76" class="person-' + message.person + '-avatar" src="' + gravatar_url(people[message.person].gravatar_hash, 76) + '" data-avatar-size="76" alt="" />' + message.message
                });
                var new_msg_fx = new Fx.Tween(new_msg, {
                    'property': 'margin-top',
                    'onComplete': function() {
                        timeout = window.setTimeout(next_message, 5000);
                    }
                });
                new_msg_fx.set(-128);
                new_msg.inject($('news'));
                new_msg_fx.start(0);
                
                current_index += 1;
                if (current_index >= queue.length) {
                    current_index = 0;
                }
            };
            
            var old_msg = $('msg');
            var old_msg_fx = null;
            if (old_msg !== null) {
                old_msg_fx = new Fx.Tween(old_msg, {
                    'property': 'margin-top',
                    'onComplete': function() {
                        old_msg.destroy();
                        show_new_msg();
                    }
                });
                old_msg_fx.start(128)
            } else {
                show_new_msg();
            }
        };
        
        return {
            'add': function(item) {
                queue.unshift(item);
                current_index = 0;
                for(var i = 0; i < queue.length - 5; i++) {
                    queue.pop();
                }
                
                if (timeout === null) {
                    next_message();
                }
            },
            'init': function(items) {
                queue = [];
                Object.each(items, function(item, index) {
                    queue.push(item);
                });
            },
            'start': function() {
                if (timeout === null) {
                    next_message();
                }
            },
            'stop': function() {
                if (timeout !== null) {
                    window.clearTimeout(timeout);
                    timeout = null;
                }
            }
        }
    })();
    
    var message_handlers = {
        'pinger': function(data) {
            $('present').getElement('strong').set('text', data.active);
            $('absent').getElement('strong').set('text', data.inactive);
        },
        'xmpp': function(data) {
            if (data.hasOwnProperty('person') === false) {
                xmpp_queue.init(data);
                xmpp_queue.start();
            } else {
                xmpp_queue.add(data);
            }
        },
        'redmine': function(data) {
            var count = 0;            
            var row_class = 'odd';
            
            var make_row = function(entry) {
                var row = new Element('tr', {
                    'class': row_class,
                    'id': 'project-' + entry.id,
                    'data-project-id': entry.id
                });
                
                var cell_name = new Element('td', {
                    'class': 'name',
                    'text': entry.name
                });
                cell_name.inject(row);
                
                var cell_name = new Element('td', {
                    'class': 'name',
                    'text': entry.name
                });
                
                var tasks_total = entry.issues['2'].open + entry.issues['2'].closed;
                var tasks_cell = new Element('td', {
                    'class': 'tasks',
                    'html': entry.issues['2'].open + ' open / <span>' + tasks_total + '</stats>'
                });
                tasks_cell.inject(row);
                
                var errors_total = entry.issues['1'].open + entry.issues['1'].closed;
                var errors_cell = new Element('td', {
                    'class': 'errors',
                    'html': entry.issues['1'].open + ' open / <span>' + errors_total + '</stats>'
                });
                errors_cell.inject(row);
                
                var people_cell = new Element('td', {
                    'class': 'persons',
                    'html': '<ul></ul>'
                });
                people_cell.inject(row);
                people_list = people_cell.getElement('ul');
                
                Array.each(entry.people, function(item, index) {
                    var person_item = new Element('li', {
                        'html': '<img width="60" height="60" class="person-' + item + '-avatar" src="' + gravatar_url(people[item].gravatar_hash) + '" data-avatar-size="60" alt="" /><span class="person-' + item + '-name">' + people[item].name + '</span>'
                    });
                    person_item.inject(people_list);
                });
                
                return row;
            };
            
            window.clearTimeout(projects_scroll_timeout);
            var projects_table = $('projects').getElement('tbody');
            projects_table.empty();
            $('projects').setStyle('top', 0);
            Array.each(data.projects, function(item, index) {
                var new_row = make_row(item);
                
                new_row.inject(projects_table);
                
                count += 1;
                row_class = (row_class === 'odd') ? 'even' : 'odd';
            });
            
            $('projects_count').getElement('strong').set('text', count);
            projects_scroll_timeout = window.setTimeout(scroll_projects, 5000);
        },
        'weather': function(data) {
            var container = $('weather');
            container.getElement('img').set({
                'src': '/static/weather-icons/' + data.icon_code + '.png',
                'alt': data.description,
                'title': data.description
            });
            container.getElement('strong').set('text', data.temperature + '°' + data.temperature_unit);
            container.getElement('span').set('text', data.city);
        }
    };
    
    var scroll_projects = function() {
        var content = $('content'),
            table = $('projects'),
            content_size = content.getSize(),
            table_size = table.getSize(),
            table_position = table.getPosition(content),
            new_top = 0,
            fx = null;
        
        window.clearTimeout(projects_scroll_timeout);
        if (table_size.y > content_size.y) {
            if (table_position.y == 0) {
                new_top = -1 * (table_size.y - content_size.y);
            } else {
                new_top = 0;
            }
            
            fx = new Fx.Tween(table, {
                'property': 'top',
                'onComplete': function() {
                    projects_scroll_timeout = window.setTimeout(scroll_projects, 5000);
                }
            });
            fx.start(new_top);
        }
    };
    
    var h4x0r_people = function() {
        Object.each(people, function(value, key) {
            Array.each($$('img.person-' + key + '-avatar'), function(item, index) {
                $(item).set('src', gravatar_url(value.gravatar_hash, $(item).get('data-avatar-size')));
            });
            Array.each($$('.person-' + key + '-name'), function(item, index) {
                $(item).set('text', value.name);
            });
        });
    };
    
    window.addEvent('domready', function() {
        load_people(function() {
            var queue = [ 'pinger', 'xmpp', 'redmine', 'weather' ];
            
            var queue_done = function() {
                var event_source = new BTHEventSource('/events');
                
                event_source.message('pinger', message_handlers.pinger);
                event_source.message('xmpp', message_handlers.xmpp);
                event_source.message('redmine', message_handlers.redmine);
                event_source.message('weather', message_handlers.weather);
                event_source.message('sysmsg', function(data) {
                    if (data == 'h4x0r_people') {
                        load_people(h4x0r_people);
                    }
                });
                event_source.start();
                
                var blanker_timeout = null;        
                
                var hide_blanker = function() {
                    window.clearTimeout(blanker_timeout);
                    $('blanker').removeClass('visible');
                    blanker_timeout = window.setTimeout(show_blanker, 2*60*1000);
                };
                        
                var show_blanker = function() {
                    window.clearTimeout(blanker_timeout);
                    $('blanker').addClass('visible');
                    blanker_timeout = window.setTimeout(hide_blanker, 5*1000);
                };
                
                hide_blanker();
            };
            
            var load_status = function(channel, callback) {
                channel = channel || null;
                callback = callback || function() {};
                
                if (channel === null)
                {
                    return false;
                }
                
                var request = new Request.JSON({
                    'url': '/status/' + channel,
                    'method': 'GET',
                    'onFailure': function() {
                        ajax_error();
                        queue_next();
                    },
                    'onSuccess': function(data) {
                        if (data != null) {
                            callback(data);
                        }
                    }
                }).send();
                
                return true;
            };
            
            var queue_next = function() {
                var job = queue.shift();
                
                if (job === undefined) {
                    queue_done();
                } else {
                    console.log(job);
                    load_status(job, function(data) {
                        message_handlers[job].apply(message_handlers, [ data ]);
                        queue_next();
                    });
                }
            };
            queue_next();
        });
    });
})();