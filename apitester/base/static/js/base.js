$(document).ready(function($) {
	$('#authentication-select').change(function() {
		$('.authentication-method').hide();
		var method = $(this).val();
		$(`#authenticate-${method}`).show();
	});
});
