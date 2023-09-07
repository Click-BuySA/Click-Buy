  $(document).ready(function () {
    // Initialize an array to store the selected property IDs
    var selectedProperties = [];

  // Event handler for sending selected properties via email
  $('.send-email-link').on('click', function (event) {
    event.preventDefault(); // Prevent the default anchor behavior


    // Check if any property is selected
    if (selectedProperties.length > 0) {
      // Construct an array of selected property details
      var selectedPropertyDetails = selectedProperties.map(function (propertyId) {
        var propertyRow = $('.property-checkbox[data-property-id="' + propertyId + '"]').closest('tr');
        return {
          id: propertyId,
          description: propertyRow.find('.clickable-property-desc').text(),
          price: propertyRow.find('[data-column="price"]').text(),
          beds: propertyRow.find('[data-column="bedrooms"]').text(),
          baths: propertyRow.find('[data-column="bathrooms"]').text(),
          garages: propertyRow.find('[data-column="garages"]').text(),
          link: propertyRow.find('a.btn-primary').attr('href'),
          link_display: propertyRow.find('a.btn-primary').text(),
        };
      });

      // Send the AJAX request with the selected property details
      $.ajax({
        url: '/send_email',
        method: 'POST',
        data: JSON.stringify(selectedPropertyDetails),
        contentType: 'application/json',
        success: function (response) {
          if (response.message === "success") {
            // Show success alert message
            alert("Export successful to " + response.email);
          } else {
            // Show error alert message
            alert("Export failed. Please contact an administrator.");
          }
        },
        error: function (error) {
          console.log("Email error:", error);

          // Show error alert message
          alert("Export failed. Please contact an administrator.");
        }
      });
    } else {
      // Show info alert message
      alert("No properties selected.");
    }
  });

  // Event handler for the "Select All" checkbox
  $('#select_all_properties').on('change', function () {
    var isChecked = $(this).prop('checked');

    // Find and update all individual property checkboxes
    $('.property-checkbox').prop('checked', isChecked);

    // Update selectedProperties based on all checkboxes
    if (isChecked) {
      selectedProperties = $('.property-checkbox').map(function () {
        var propertyId = parseInt($(this).data('property-id'));
        return !isNaN(propertyId) ? propertyId : null;
      }).get();
    } else {
      selectedProperties = [];
    }
  });

  // Event handler for individual property checkboxes
  $(document).on('change', '.property-checkbox', function () {
    var propertyId = parseInt($(this).data('property-id'));

    if (this.checked) {
      // Add property ID to selectedProperties if not already added
      if (!isNaN(propertyId) && selectedProperties.indexOf(propertyId) === -1) {
        selectedProperties.push(propertyId);
      }
    } else {
      // Remove property ID from selectedProperties
      var index = selectedProperties.indexOf(propertyId);
      if (index !== -1) {
        selectedProperties.splice(index, 1);
      }
    }
  });

    // Event listener for form submission
    document.getElementById('filter-form').addEventListener('submit', function (event) {
      const minPriceInput = document.getElementById('min_price_filter');
      const maxPriceInput = document.getElementById('max_price_filter');

      if (minPriceInput.value !== 0 && maxPriceInput.value !== 0 && Number(minPriceInput.value) > Number(maxPriceInput.value)) {
        event.preventDefault();
        alert('Min price cannot be greater than max price.');
      }
    });

    // Event listener for pagination links
    $(document).on('click', '.pagination-link', function (e) {
      e.preventDefault();
      var page = $(this).data('page');
      var formData = new FormData(document.getElementById('filter-form'));
      handlePaginationClick(page, formData);
    });

    // Event listener for the "Filter" button click
    $('#filter-button, #filter-button-hidden').on('click', function (e) {
      e.preventDefault();
      handleFormSubmit();
    });

    // Event listener for the "Reset Filters" button click
    $('#reset-filters, #reset-filters-hidden').on('click', function (event) {
      event.preventDefault(); // Prevent the default behavior
      resetFilters();
    });


    $("#expand-toggle-btn").click(function () {
      $(".expandable-column").toggle();
      $('#properties-table').sortTable();
    });

    // Set the selected areas in the dropdown
    $('.js-example-basic-multiple').val(selectedAreas);
    $('.js-example-basic-multiple').trigger('change'); // Refresh the dropdown to display selected values

    // Initial page load
    var formData = new FormData(document.getElementById('filter-form'));
    handlePaginationClick(1, formData);

    // Attach event listener to form fields
    $('.filter-form input, .filter-form select').on('change', function () {
      updatePaginationLinks();
    });
  });


  function handlePaginationClick(page, formData) {
    $.ajax({
      type: 'POST',
      url: '/dashboard?page=' + page,
      data: formData,
      contentType: false,
      processData: false,
      dataType: 'json',
      success: function (data) {
        updateProperties(data);
        updatePaginationControls(data.pagination.paginationHTML);
        updatePaginationLinks(); // Add this line to update the pagination links
      },
      error: function (error) {
        console.error('Error fetching properties:', error);
      }
    });
  }

  // Function to update properties and pagination
  function updateProperties(data) {  
  // Update properties in #properties_table tbody
      var propertiesBody = $('#properties_table tbody');
      propertiesBody.empty();

      for (var i = 0; i < data.properties.length; i++) {
        var property = data.properties[i];
        var row = $('<tr>');

        row.append($('<td>').html(
          '<div class="form-check form-check-muted m-0">' +
          '<label class="form-check-label">' +
          '<input type="checkbox" class="form-check-input property-checkbox" data-property-id="' + property.id + '">' +
          '<i class="input-helper"></i>' +
          '</label>' +
          '</div>'
        ));
      
        // Add the classes for responsiveness
        var tableResponsive = $('<div>', {
          class: 'table-responsive table-responsive-sm table-responsive-md table-responsive-lg table-responsive-xl'
        });
        var table = $('<table>', {
          class: 'table'
        });
        // Append the table to the table-responsive container
        tableResponsive.append(table);

        // Append the table-responsive container to propertiesBody
        propertiesBody.append(tableResponsive);
        
        // Property Description
        var propertyDesc = '';
        if (property.street_number) {
            propertyDesc += property.street_number + ' ';
        }
        if (property.street_name) {
            propertyDesc += property.street_name + ' ';
        }
        if (property.complex_number) {
            propertyDesc += property.complex_number + ' ';
        }
        if (property.complex_name) {
            propertyDesc += property.complex_name;
        }

        if (propertyDesc === '') {
            propertyDesc = 'No description available'; // Fallback text
        }

        // Wrap the property description in an anchor tag
        var propertyDescLink = $('<a>', {
            href: '/view_property/' + property.id, // Modify this URL as needed
            class: 'clickable-property-desc',
            text: propertyDesc
        });

        var descriptionCell = $('<td>', {
            'data-column': 'prop_desc'
        }).append(propertyDescLink);

        row.append(descriptionCell);
        
        // Other columns
        var areaCell = $('<td>', {
            'data-column': 'area'
        }).text(property.area);
        row.append(areaCell);
        
        // Price column without decimals
        var priceFormatted = 'R ' + numberWithCommas(Math.floor(property.price));
        var priceCell = $('<td>', {
            'data-column': 'price' // Add the data-column attribute
        }).text(priceFormatted);
        row.append(priceCell);

        // Bedrooms column
        var bedroomsCell = $('<td>', {
            'data-column': 'bedrooms' // Add the data-column attribute
        }).text(property.bedrooms);
        row.append(bedroomsCell);

        // Bathrooms column
        var bathroomsCell = $('<td>', {
            'data-column': 'bathrooms' // Add the data-column attribute
        }).text(property.bathrooms);
        row.append(bathroomsCell);

        // Garages column
        var garagesCell = $('<td>', {
            'data-column': 'garages' // Add the data-column attribute
        }).text(property.garages);
        row.append(garagesCell);

        
        // P-24 Link
        var p24Link = $('<a>', {
          class: 'btn btn-primary',
          href: property.link,
          target: '_blank',
          text: property.link_display
        });
        row.append($('<td>').append(p24Link));

        // Expandable columns
        row.append($('<td>', {
            'data-column': 'swimming_pool' // Add the data-column attribute
        }).text(property.swimming_pool).addClass('expandable-column'));

        row.append($('<td>', {
            'data-column': 'garden_flat' // Add the data-column attribute
        }).text(property.garden_flat).addClass('expandable-column'));

        row.append($('<td>', {
            'data-column': 'study' // Add the data-column attribute
        }).text(property.study).addClass('expandable-column'));

        row.append($('<td>', {
            'data-column': 'ground_floor' // Add the data-column attribute
        }).text(property.ground_floor).addClass('expandable-column'));

        row.append($('<td>', {
            'data-column': 'pet_friendly' // Add the data-column attribute
        }).text(property.pet_friendly).addClass('expandable-column'));

        propertiesBody.append(row);
      }
    }

  function handleFormSubmit() {
    var minPriceValue = parseFloat($('#min_price_filter').val().replace(/\D/g, ''));
    var maxPriceValue = parseFloat($('#max_price_filter').val().replace(/\D/g, ''));

    if (minPriceValue !== '' && maxPriceValue !== '' && parseInt(minPriceValue) > parseInt(maxPriceValue)) {
      alert("Minimum price cannot be higher than maximum price.");
    } else {

      var formData = new FormData(); // Create a new FormData object
      formData.append('street_name_filter', $('[name="street_name_filter"]').val());
      formData.append('complex_name_filter', $('[name="complex_name_filter"]').val());

      // Convert max and min price to numeric values
      var minPriceValue = parseFloat($('#min_price_filter').val().replace(/\D/g, ''));
      var maxPriceValue = parseFloat($('#max_price_filter').val().replace(/\D/g, ''));
      if (!isNaN(minPriceValue)) {
          formData.append('min_price_filter', minPriceValue);
      }

      if (!isNaN(maxPriceValue)) {
          formData.append('max_price_filter', maxPriceValue);
      }

      formData.append('area_filter', $('[name="area_filter"]').val());
      formData.append('max_price_filter', $('[name="max_price_filter"]').val());
      formData.append('number_filter', $('[name="number_filter"]').val());
      formData.append('bedroom_filter', $('[name="bedroom_filter"]').val());
      formData.append('bathroom_filter', $('[name="bathroom_filter"]').val());
      formData.append('garages_filter', $('[name="garages_filter"]').val());

      // Handle checkboxes
      if ($('#study_filter').prop('checked')) {
          formData.append('study_filter', 'true');
      }
      if ($('#swimming_pool_filter').prop('checked')) {
          formData.append('swimming_pool_filter', 'true');
      }
      if ($('#ground_floor_filter').prop('checked')) {
          formData.append('ground_floor_filter', 'true');
      }
      if ($('#garden_flat_filter').prop('checked')) {
          formData.append('garden_flat_filter', 'true');
      }
      if ($('#pet_friendly_filter').prop('checked')) {
          formData.append('pet_friendly_filter', 'true');
      }
      
      handlePaginationClick(1, formData); // Send the form data along with page number
    }  
  }
    
  function updatePaginationLinks() {
    var formData = new FormData($('.filter-form')[0]); // Construct FormData object
    
    // Construct the URLSearchParams manually
    var params = [];
    formData.forEach(function(value, key){
      params.push(key + '=' + encodeURIComponent(value));
    });
    var queryString = params.join('&');

    var paginationLinks = $('.dynamic-pagination-link');
    if (paginationLinks.length === 1) {
      var page = paginationLinks.data('page');
      var newHref = '/dashboard?page=' + page + '&' + queryString;
      paginationLinks.attr('href', newHref);
    } else {
      paginationLinks.each(function () {
        var page = $(this).data('page');
        var newHref = '/dashboard?page=' + page + '&' + queryString;
        $(this).attr('href', newHref);
      });
    }
  }

  function resetFilters() {
      // Reset filter input values
      $('[name="street_name_filter"]').val("");
      $('[name="complex_name_filter"]').val("");
      $('[name="number_filter"]').val("");
      $('[name="area_filter"]').val("");
      $('[name="max_price_filter"]').val(0);  // Reset the value directly
      $('[name="min_price_filter"]').val(0);  // Reset the value directly
      $('[name="bedroom_filter"]').val("");
      $('[name="bathroom_filter"]').val("");
      $('[name="garages_filter"]').val("");
      $('#study_filter').prop('checked', false);
      $('#swimming_pool_filter').prop('checked', false);
      $('#ground_floor_filter').prop('checked', false);
      $('#garden_flat_filter').prop('checked', false);
      $('#pet_friendly_filter').prop('checked', false);

      minPriceAutoNumeric.clear();
      maxPriceAutoNumeric.clear();


      // Make an AJAX request to clear filters and update the table
      $.ajax({
          url: '/dashboard',  // Use the /dashboard route for clearing filters
          method: 'POST',
          data: {
              reset_filters: true 
          },
          success: function(data) {
              // Update the table using the data received from the server
              updateProperties(data);
              // Generate new pagination HTML based on the updated data
              updatePaginationControls(data.pagination.paginationHTML)
              // Clear the filter form inputs after successful response
              $('#filter-form')[0].reset();
              // Clear the selected areas in the dropdown for area filters
              $('.js-example-basic-multiple').val([]); // Set an empty array to clear selection
              $('.js-example-basic-multiple').trigger('change'); // Refresh the dropdown to clear selected values
          },
          error: function(error) {
              console.error('Error clearing filters:', error);
          }
      });
    }

  function numberWithCommas(number) {
    return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }

  function updatePaginationControls(paginationHTML) {
    // Create a jQuery object from the paginationHTML
    var paginationContent = $(paginationHTML);
    // Get the new pagination container
    var newPaginationContainer = $('#new-pagination-container');
    // Empty the new pagination container and insert the pagination content
    newPaginationContainer.empty().append(paginationContent);
    // Add a class to each pagination link
    newPaginationContainer.find('.pagination-link').addClass('dynamic-pagination-link');
  }