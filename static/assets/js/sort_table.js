$(document).ready(function() {
    const sortIcons = {
        'asc': '<i class="mdi mdi-sort-ascending"></i>',
        'desc': '<i class="mdi mdi-sort-descending"></i>'
    };
    const sortDirection = {};

    $('.sort-header').on('click', function() {
        const column = $(this).data('column');
        const currentOrder = $(this).data('order') || 'asc'; 

        //toggle sorting direction
        const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';

        //remove icons from other headers
        $('.sort-header').not(this).data('order', null).find('.sort-icon').html('');

        //set icon for clicked header
        $(this).data('order', newOrder).find('.sort-icon').html(sortIcons[newOrder]);
        sortTable(column, $(this).closest('table'));
    });

    function sortTable(column, table) {
        const rows = table.find('tbody tr').toArray();

        if (!sortDirection[column] || sortDirection[column] === 'desc') {
            rows.sort((a, b) => compareRows(a, b, column));
            sortDirection[column] = 'asc';
        } else {
            rows.sort((a, b) => compareRows(b, a, column));
            sortDirection[column] = 'desc';
        }

        table.find('tbody').empty().append(rows);
    }

    function compareRows(a, b, column) {
        const valA = $(a).find(`td[data-column="${column}"]`).text().toUpperCase();
        const valB = $(b).find(`td[data-column="${column}"]`).text().toUpperCase();

        return valA.localeCompare(valB);
    }
});