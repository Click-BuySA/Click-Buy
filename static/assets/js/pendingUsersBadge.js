function updatePendingUsersBadge() {
    $.get('/get_pending_users_count', function(data) {
        if (data.pending_users > 0) {
            $('#newUsersBadgeContainer').find('.badge').text(data.pending_users).show();
        } else {
            $('#newUsersBadgeContainer').find('.badge').hide();
        }
    });
}

$(document).ready(function() {
  updatePendingUsersBadge();
});