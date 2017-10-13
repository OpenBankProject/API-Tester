$(document).ready(function($) {
	$('#authentication-select').change(function() {
		$('.authentication-method').hide();
		var method = $(this).val();
		console.log(`#authentication-${method}`);
		$(`#authenticate-${method}`).show();
	});
});
