$(function() {
	function runTest(test) {
		var url = URL_RUNTEST_BASE.replace('all', test);
		$.get(url, function (data) {
			if (data['success']) {
				alertType = 'success';
				msg = '';
			} else {
				alertType = 'danger';
				msg = '<ul>';
				for (var i=0; i < data['messages'].length; i++) {
					msg += `<li>${data['messages'][i]}</li>`;
				}
				msg += '</ul>';
			}
			$('#results').append(`<div class="alert alert-${alertType}">${data['config']['summary']}<br />${data['test']}<br />${msg}<br />${data['result']}<br />Took ${data['execution_time']} ms</div>`);
		});
	}

	$('#run').click(function() {
		$('#results').empty();
		var runners = $('.runner');
		for (var i=0; i < runners.length; i++) {
			var runner = $(runners[i]);
			if (runner.find('input').is(':checked')) {
				runTest(runner.data('test'));
			}
		}
	});
	$('.runner button').click(function() {
		$('#results').empty();
		var test = $(this).parent().parent().parent().data('test');
		runTest(test);
	});

	$('#checkNone').click(function() {
		$('.runner').find('input').prop('checked', false);
	});
	$('#checkAll').click(function() {
		$('.runner').find('input').prop('checked', true);
	});

});
