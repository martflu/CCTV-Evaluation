$(document).ready(function() {
	start();
});

function start() {
	var file_size = 0;
	// max file size = 100 MB
	//104857600;
	var max_file_size = 104857600;
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
			log_error("File size too large! Selected file was to large by: " + bytesToSize(file_size - max_file_size));
			show_element($('#file_upload_error'));
			hide_element($('#file_upload_error'), 2000);
			$('#video_upload_button').prop('disabled', true);
			$('#file_upload').fileupload('reset');
		} else {
			$('#video_upload_button').prop('disabled', false);
			set_progress_bar_percent($('#progress_upload_bar'), 0);
		}
	});

	$('#video_upload_button').click(function() {
		$("#file_upload_form").submit();
		upload_start();
	});

	$('#file_upload_form').submit(function(e) {
		var form_data = new FormData();
		form_data.append('video_file', $("#video_file")[0].files[0]);
		var file = $("#video_file")[0].files[0];
		var xhr = new XMLHttpRequest();

		xhr.addEventListener('progress', function(e) {
			var done = e.position || e.loaded, total = e.totalSize || e.total;
		}, false);

		xhr.addEventListener('load', function(e) {
			set_progress_bar_percent($('#progress_upload_bar'), 100);
			$('#progress_upload').removeClass('progress-striped');
			clearInterval(interval);
			var file_name = file.name;
			$.get("/convert?filename=" + file_name, function(data) {
				upload_finished();
				interval = setInterval(get_conversion_progress, 100);
			});

		}, false);

		if (xhr.upload) {
			xhr.upload.onprogress = function(e) {
				var done = e.position || e.loaded, total = e.totalSize || e.total;
				var percent = (Math.floor(done / total * 1000) / 10);
				set_progress_bar_percent($('#progress_upload_bar'), percent / 2);
				log('file upload client side: ' + bytesToSize(done) + ' of ' + bytesToSize(total) + ' = ' + percent + '% ' + bytesToSize(total - done) + ' missing');
				if (percent === 100) {
					interval = setInterval(get_upload_progress, 500);
				}
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

	function get_conversion_progress() {
		$.get("/conversionprogress", function(data) {
			var percent = parseFloat(data);
			set_progress_bar_percent($('#progress_conversion_bar'), percent);
			log('video to frames conversion: ' + percent + '%');
			if (percent === 100) {
				clearInterval(interval);
				conversion_finished();
			}
		});
	}

	function get_upload_progress() {
		$.get("/uploadprogress", function(data) {
			upload_progress = data;
			var percent = (Math.floor(upload_progress / file_size * 1000) / 10);
			set_progress_bar_percent($('#progress_upload_bar'), 50 + percent / 2);
			log('file upload server side: ' + bytesToSize(upload_progress) + ' of ' + bytesToSize(file_size) + ' = ' + percent + '% ' + bytesToSize(file_size - upload_progress) + ' missing');
		});
	}

}

function upload_start() {
	$('#video_upload_button').prop('disabled', true);
	$('#file_upload').fileupload('reset');
	$('#badge_upload').addClass('badge-info');
	$('#task_table').show();
}

function upload_finished() {
	$('#badge_upload').removeClass('badge-info');
	$('#badge_upload').addClass('badge-success');
	conversion_start();
}

function conversion_start() {
	$('#badge_conversion').addClass('badge-info');
}

function conversion_finished() {
	$('#badge_conversion').removeClass('badge-info');
	$('#badge_conversion').addClass('badge-success');
	evaluation_start();
}

function evaluation_start() {
	$('#badge_evaluation').addClass('badge-info');
}

function evaluation_finished() {
	
}

function log(message) {
	$('#console').append("<p class='log'>" + message + "</p>");
	$('#console').scrollTop($('#console')[0].scrollHeight);
};

function log_warning(message) {
	$('#console').append("<p class='text-warning log'>" + message + "</p>");
	$('#console').scrollTop($('#console')[0].scrollHeight);
};

function log_error(message) {
	$('#console').append("<p class='text-error log'>" + message + "</p>");
	$('#console').scrollTop($('#console')[0].scrollHeight);
};

function bytesToSize(bytes) {
	var sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
	if (bytes == 0)
		return 'n/a';
	var i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
	return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
};

function hide_element(element, delay) {
	setTimeout(function() {
		element.css({
			opacity : 1.0,
			visibility : "visible"
		}).animate({
			opacity : 0.0
		});
	}, delay);
};

function show_element(element) {
	element.css({
		opacity : 0.0,
	}).animate({
		opacity : 1.0
	});
};

function set_progress_bar_percent(progess_bar, percent) {
	progess_bar.css('width', percent + '%');
};
