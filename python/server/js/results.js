$(document).ready(function() {
    start();
});

function start() {
    $('.panel-heading').click(section_clicked);
    $('.progress_bar_selection').click(progress_bar_selection_clicked);
    $('#carousel-example-generic').carousel('pause');
    $('#carousel-example-generic').on('slide.bs.carousel', function(event) {
        var carousel_inner = $(event.target).find('.carousel-inner');
        var active_slide = carousel_inner.find('.active');
        var index = active_slide.attr('index');
        var progress = $('#progress_selection');
        var active_progress = $($('#progress_selection').children()[index]);
        active_progress.removeClass('active');
    });
    $('#carousel-example-generic').on('slid.bs.carousel', function(event) {
        var carousel_inner = $(event.target).find('.carousel-inner');
        var active_slide = carousel_inner.find('.active');
        var index = active_slide.attr('index');
        var progress = $('#progress_selection');
        var active_progress = $($('#progress_selection').children()[index]);
        active_progress.addClass('active');
        $('#carousel-example-generic').carousel('pause');
        update_frame_info(index);
    });
    update_frame_info(0);
}

function section_clicked(event) {
    heading = $(event.target).closest('.panel-heading');
    if (heading.is('.panel-heading')) {
        span = heading.find('span');
        if (span.hasClass('glyphicon-chevron-right')) {
            span.removeClass('glyphicon-chevron-right');
            span.addClass('glyphicon-chevron-down');
        } else {
            span.removeClass('glyphicon-chevron-down');
            span.addClass('glyphicon-chevron-right');
        }
        parent = heading.parent();
        body = parent.find('.panel-body');
        body.toggle();
    }
}

function progress_bar_selection_clicked(event) {
    var target = $(event.target);
    var index = parseInt(target.attr('index'), 10);
    $('#carousel-example-generic').carousel(index);
    update_frame_info(index);
}

function update_frame_info(index) {
    var detected_string = '';
    if (detected[index]) {
        detected_string = 'Yes';
    } else {
        detected_string = 'No';
    }
    $('#detected').html(detected_string);
    $('#faces').html(faces[index]);
    var width = Math.sqrt(area[index]).toFixed();
    $('#area').html(area[index] + " pixels (" + width + "x" + width + ")");
    $('#min').html(min[index]);
    $('#mean').html(mean[index]);
    $('#max').html(max[index]);
}
