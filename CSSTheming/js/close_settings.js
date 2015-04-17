/**
 * Created by justin on 4/17/15.
 */
function close_settings_section() {
    $('.settings .settings-section-title').removeClass('active');
    $('.settings .settings-section-content').slideUp(300).removeClass('open');
    document.getElementById("main").style.visibility = "visible";
}
$(document).ready(function() {
    $('.settings-section-title').click(function(e) {
        var currentAttrValue = $(this).attr('href');
        if($(e.target).is('.active')) {
            close_settings_section();
        }else {
            $(this).addClass('active');
            $('.settings-section-content').slideUp(300).removeClass('open');
            $('.settings ' + currentAttrValue).slideDown(300).addClass('open');
            document.getElementById("main").style.visibility = "hidden";
        }
        e.preventDefault();
    });
});