$(function() {
	function runTest(runner) {
		var test = runner.data('test')
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
			var result = `<div class="alert alert-${alertType}">${data['config']['summary']}<br />${data['test']}<br />${msg}<br /><pre>${data['result']}</pre><br />Took ${data['execution_time']} ms</div>`;
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
	$('.runner button').click(function() {
		var runner = $(this).parent().parent().parent();
		$(runner).find('.result').empty();
		runTest(runner);
	});

	$('#checkNone').click(function() {
		$('.runner').find('input').prop('checked', false);
	});
	$('#checkAll').click(function() {
		$('.runner').find('input').prop('checked', true);
	});

});
