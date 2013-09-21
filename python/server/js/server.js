$(document).ready(function() {
	start();
});

function start() {
	var file_size = 0;
	// max file size = 20 MB
	//20971520;
	var max_file_size = 20971520;
	var file_size = 0;
	var upload_progress = 0;

	var interval;

	$('#video_file').bind('change', function(test) {
		if (this.files.length === 0) {
			$('#video_upload_button').prop('disabled', true);
			log_warning("No file selected.");
			return;
		}
		file_size = this.files[0].size;
		log("Selected file size: " + bytesToSize(file_size));
		if (file_size > max_file_size) {
			$('#file_upload_error_text').text("File size too large!");
			$('#file_upload_error').css({
				opacity : 0.0,
				visibility : "visible"
			}).animate({
				opacity : 1.0
			});
			log_error("File size too large! Selected file was to large by: " + bytesToSize(file_size - max_file_size));
			setTimeout(function() {
				$('#file_upload_error').css({
					opacity : 1.0,
					visibility : "visible"
				}).animate({
					opacity : 0
				}, 200);
			}, 1500);
			$('#video_upload_button').prop('disabled', true);
			$('#file_upload').fileupload('reset');
		} else {
			$('#video_upload_button').prop('disabled', false);
			$('#progress_bar').css('width', '0%');
		}
	});

	$('#video_upload_button').click(function() {
		$("#file_upload_form").submit();

		$('#video_upload_button').prop('disabled', true);
		$('#file_upload').fileupload('reset');

	});

	$('#file_upload_form').submit(function(e) {
		$('#progress').css({
			opacity : 0.0,
			visibility : "visible"
		}).animate({
			opacity : 1.0
		});
		var form_data = new FormData();
		form_data.append('video_file', $("#video_file")[0].files[0]);
		var file = $("#video_file")[0].files[0];
		var xhr = new XMLHttpRequest();

		xhr.addEventListener('progress', function(e) {
			var done = e.position || e.loaded, total = e.totalSize || e.total;
		}, false);

		xhr.addEventListener('load', function(e) {
			$('#progress_bar').css('width', '100%');
			$('#progress').removeClass('progress-striped');

			setTimeout(function() {
				$('#progress').css({
					opacity : 1.0,
					visibility : "visible"
				}).animate({
					opacity : 0.0
				});
			}, 2000);
			clearInterval(interval);
		}, false);

		if (xhr.upload) {
			xhr.upload.onprogress = function(e) {
				var done = e.position || e.loaded, total = e.totalSize || e.total;
				var percent = (Math.floor(done / total * 1000) / 10);
				$('#progress_bar').css('width', percent / 2 + '%');
				log('file upload client side: ' + bytesToSize(done) + ' of ' + bytesToSize(total) + ' = ' + percent + '% ' + bytesToSize(total - done) + ' missing');
			};

			xhr.upload.onload = function(e) {
				interval = setInterval(get_upload_progress, 1000);
			};
		}

		xhr.open('post', "/upload", true);
		xhr.send(form_data);
		e.preventDefault();
	});

	$('#terminal_icon').click(function() {
		$('#console').slideToggle();
		$('#console').scrollTop($('#console')[0].scrollHeight);
	});

	function get_upload_progress() {
		$.get("/uploadprogress", function(data) {
			upload_progress = data;
			var percent = (Math.floor(upload_progress / file_size * 1000) / 10);
			$('#progress_bar').css('width', 50 + percent / 2 + '%');
			log('file upload server side: ' + bytesToSize(upload_progress) + ' of ' + bytesToSize(file_size) + ' = ' + percent + '% ' + bytesToSize(file_size - upload_progress) + ' missing');
		});
	}

}

function log(message) {
	$('#console').append("<p class='log'>" + message + "</p>");
	$('#console').scrollTop($('#console')[0].scrollHeight);
}

function log_warning(message) {
	$('#console').append("<p class='text-warning log'>" + message + "</p>");
	$('#console').scrollTop($('#console')[0].scrollHeight);
}

function log_error(message) {
	$('#console').append("<p class='text-error log'>" + message + "</p>");
	$('#console').scrollTop($('#console')[0].scrollHeight);
}

function bytesToSize(bytes) {
	var sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
	if (bytes == 0)
		return 'n/a';
	var i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
	return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
};