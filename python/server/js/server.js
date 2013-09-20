window.onload = function() {
	start();
};

function start() {
	var file_size = 0;
	
	$('#video_file').bind('change', function() {
		file_size = this.files[0].size;
		alert(file_size);
		$('#videoUploadButton').prop('disabled', false);
	});

	$('#videoUploadButton').click(function() {
		alert("here is the upload");
	});

}

