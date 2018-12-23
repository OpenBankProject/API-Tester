$(function() {
	function escapeHTML(s) {
		return String(s).replace(/&(?!\w+;)/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
	}

	function runTest(runner) {
		//var testpath = runner.data('testpath');
		testmethod = runner.data('testmethod');
        testconfig_pk = runner.data('testconfig_pk');
        operationId = runner.data('operationId');
        path = $(runner).find('input[name="urlpath"]').val();
		testpath = 'run/' + testmethod + "/" + path + "/" + testconfig_pk  + "/"+ operationId   ;
		$.post(testpath,  {
            'json_body': runner.find('textarea').val(),
            'csrfmiddlewaretoken': window.CSRF
        }, function (data) {
			var alertType = 'success';
			var msg = '';
			var collapse = '';
			var text = `<pre>${escapeHTML(data['text'])}</pre>`;
			if (!data['success']) {
				alertType = 'danger';
				msg = '<ul>';
				for (var i=0; i < data['messages'].length; i++) {
					msg += `<li>${data['messages'][i]}</li>`;
				}
				msg += '</ul>';
			} else {
				collapse = `<button type="button" class="btn btn-xs btn-success pull-right" data-toggle="collapse" data-target="#${data['config']['operation_id']}" aria-expanded="false"><span class="glyphicon glyphicon-chevron-right"></span><span class="glyphicon glyphicon-chevron-down"></span></button>`;
				text = `<div id="${data['config']['operation_id']}" class="collapse">${text}</div>`;
			}
			var result = `<div class="alert alert-${alertType}"><div class="row"><div class="col-xs-10 col-sm-11">${data['config']['summary']}<br />${data['config']['urlpath']}<br />Took ${data['execution_time']} ms<br />${msg}</div><div class="col-xs-2 col-sm-1">${collapse}</div></div>${text}</div>`;
			$(runner.find('.result')).append(result);
		});
	}

	$('#run').click(function() {
		$('.result').empty();
		var runners = $('.runner');
		for (var i=0; i < runners.length; i++) {
			var runner = $(runners[i]);
			if (runner.find('input').is(':checked')) {
				runTest(runner);
			}
		}
	});
	$('.runner button.forTest').click(function() {
		var runner = $(this).parent().parent().parent();
		$(runner).find('.result').empty();
		runTest(runner);
	});
    $('.runner button.forSave').click(function() {
    	var t = $(this)
        var runner = $(this).parent().parent().parent();
        jsonBody = $(runner).find('textarea[name="params"]').val();
		operationId = $(runner).find('input[type="hidden"]').val();
		order = $(runner).find('input[name="order"]').val();
		urlpath = $(runner).find('input[name="urlpath"]').val();
		replica_id = $(runner).find('input[name="replica_id"]').val();
		remark = $(runner).find('textarea[name="remark"]').val();

        $.post('/runtests/save/json_body', {
        	'json_body': jsonBody,
			'operation_id': operationId,
			'profile_id' : window.CURRENT_PROFILE_ID,
            'order': order,
			'urlpath': urlpath,
			'replica_id':replica_id,
			'remark':remark,
            'csrfmiddlewaretoken': window.CSRF
		}, function (response) {
        	t.next().show().fadeOut(1000);
        });

        setTimeout("window.location.reload(true)",1000);
    });

    $('.runner button.forCopy').click(function() {
        var t = $(this)
        var runner = $(this).parent().parent().parent();
        jsonBody = $(runner).find('textarea[name="params"]').val();
		operationId = $(runner).find('input[type="hidden"]').val();
		order = $(runner).find('input[name="order"]').val();
		urlpath = $(runner).find('input[name="urlpath"]').val();
		replica_id = $(runner).find('input[name="replica_id"]').val();
		remark = $(runner).find('textarea[name="remark"]').val();

        $.post('/runtests/copy/json_body', {
        	'json_body': jsonBody,
			'operation_id': operationId,
			'profile_id' : window.CURRENT_PROFILE_ID,
            'order': order,
			'urlpath': urlpath,
			'replica_id':replica_id,
			'remark':remark,
            'csrfmiddlewaretoken': window.CSRF
		}, function (response) {
        	t.next().show().fadeOut(1000);
        });

        setTimeout("window.location.reload(true)",1000);
    });

	$('#checkNone').click(function() {
		$('.runner').find('input').prop('checked', false);
	});
	$('#checkAll').click(function() {
		$('.runner').find('input').prop('checked', true);
	});

    $('#select-testconfig').change(function() {
        var configPk = $(this).val();
        if (configPk) {
            location.href = `${URL_RUNTESTS_INDEX}${configPk}`;
        } else  {
            location.href = URL_RUNTESTS_INDEX;
        }
    })

    var configPk = location.href.substr(location.href.lastIndexOf('/') + 1);
    if (configPk) {
        $('#nothing-selected').addClass('hide');
        $('#select-testconfig').val(configPk);
        $('#run-buttons').removeClass('hide');
        $('#test-list').removeClass('hide');
    }
});
