var total_pages;

$(document).ready(function () {
  // Initialize an array to store the selected property IDs
  var selectedProperties = [];
  minPriceAutoNumeric = new AutoNumeric("#min_price_filter", {
    currencySymbol: "R ",
    currencySymbolPlacement: AutoNumeric.options.currencySymbolPlacement.prefix,
    decimalPlaces: 0,
    unformatOnSubmit: true,
  });

  maxPriceAutoNumeric = new AutoNumeric("#max_price_filter", {
    currencySymbol: "R ",
    currencySymbolPlacement: AutoNumeric.options.currencySymbolPlacement.prefix,
    decimalPlaces: 0,
    unformatOnSubmit: true,
  });

  // Event listener for the "Toggle Filters" button click
  $("#toggleFilters, #toggleFilters1").click(function () {
    $("#filter-form").toggle();
    var isVisible = $("#filter-form").is(":visible");
    var buttonText = isVisible ? "Hide Filters" : "Show Filters";
    $("#toggleFilters, #toggleFilters1").text(buttonText);
  });

  // Event handler for sending selected properties via email
  $(".send-email-link").on("click", function (event) {
    event.preventDefault(); // Prevent the default anchor behavior

    // Check if any property is selected
    if (selectedProperties.length > 0) {
      // Construct an array of selected property details
      var selectedPropertyDetails = selectedProperties.map(function (
        propertyId
      ) {
        var propertyRow = $(
          '.property-checkbox[data-property-id="' + propertyId + '"]'
        ).closest("tr");
        return {
          id: propertyId,
          description: propertyRow.find(".clickable-property-desc").text(),
          price: propertyRow.find('[data-column="price"]').text(),
          beds: propertyRow.find('[data-column="bedrooms"]').text(),
          baths: propertyRow.find('[data-column="bathrooms"]').text(),
          garages: propertyRow.find('[data-column="garages"]').text(),
          link: propertyRow.find("a.btn-primary").attr("href"),
          link_display: propertyRow.find("a.btn-primary").text(),
        };
      });

      $("#loading-overlay").show();

      // Send the AJAX request with the selected property details
      $.ajax({
        url: "/send_email",
        method: "POST",
        data: JSON.stringify(selectedPropertyDetails),
        contentType: "application/json",
        success: function (response) {
          if (response.message === "success") {
            // Show success alert message
            alert("Export successful to " + response.email);
            // Hide the loading indicator when the request is complete
            $("#loading-overlay").hide();
          } else {
            // Show error alert message
            alert("Export failed. Please contact an administrator.");
            // Hide the loading indicator when the request is complete
            $("#loading-overlay").hide();
          }
        },
        error: function (error) {
          console.log("Email error:", error);
          // Hide the loading indicator when the request is complete
          $("#loading-overlay").hide();
          // Show error alert message
          alert("Export failed. Please contact an administrator.");
        },
      });
    } else {
      // Show info alert message
      alert("No properties selected.");
    }
  });

  // Event handler for the "Select All" checkbox
  $("#select_all_properties").on("change", function () {
    var isChecked = $(this).prop("checked");

    // Find and update all individual property checkboxes
    $(".property-checkbox").prop("checked", isChecked);

    // Update selectedProperties based on all checkboxes
    if (isChecked) {
      selectedProperties = $(".property-checkbox")
        .map(function () {
          var propertyId = parseInt($(this).data("property-id"));
          return !isNaN(propertyId) ? propertyId : null;
        })
        .get();
    } else {
      selectedProperties = [];
    }
  });

  // Event handler for individual property checkboxes
  $(document).on("change", ".property-checkbox", function () {
    var propertyId = parseInt($(this).data("property-id"));

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
  document
    .getElementById("filter-form")
    .addEventListener("submit", function (event) {
      // Get the numeric values using the getNumber method
      var minPriceValue = minPriceAutoNumeric.getNumber();
      var maxPriceValue = maxPriceAutoNumeric.getNumber();

      if (
        minPriceValue.valueOf !== 0 &&
        maxPriceValue.valueOf !== 0 &&
        Number(minPriceValue.valueOf) > Number(maxPriceValue.valueOf)
      ) {
        event.preventDefault();
        alert("Min price cannot be greater than max price.");
      }
    });

  // Event listener for pagination links
  $(document).on("click", ".pagination-link", function (e) {
    e.preventDefault();
    var page = $(this).data("page");
    var formData = new FormData(document.getElementById("filter-form"));
    // Parse the values
    var minPriceValue = parseFloat(
      $("#min_price_filter").val().replace(/\D/g, "")
    );
    var maxPriceValue = parseFloat(
      $("#max_price_filter").val().replace(/\D/g, "")
    );

    // Check if minPriceValue is a valid number
    if (!isNaN(minPriceValue)) {
      formData.set("min_price_filter", minPriceValue);
    } else {
      formData.set("min_price_filter", ""); // Set it to blank if it's not a valid number
    }

    // Check if maxPriceValue is a valid number
    if (!isNaN(maxPriceValue)) {
      formData.set("max_price_filter", maxPriceValue);
    } else {
      formData.set("max_price_filter", ""); // Set it to blank if it's not a valid number
    }

    handlePaginationClick(page, formData); // Pass the updated formData
  });

  // Event listener for the "Filter" button click
  $("#filter-button, #filter-button-hidden").on("click", function (e) {
    e.preventDefault();
    handleFormSubmit();
  });

  // Event listener for the "Reset Filters" button click
  $("#reset-filters, #reset-filters-hidden").on("click", function (event) {
    event.preventDefault(); // Prevent the default behavior
    resetFilters();
  });

  $("#expand-toggle-btn").click(function () {
    $(".expandable-column").toggle();
    $("#properties-table").sortTable();
  });

  // Set the selected areas in the dropdown
  $(".js-example-basic-multiple").val(selectedAreas);
  $(".js-example-basic-multiple").trigger("change"); // Refresh the dropdown to display selected values

  // Initial page load
  var formData = new FormData(document.getElementById("filter-form"));
  handlePaginationClick(1, formData);

  // Event listener for the "Jump to Page" button click
  $("#jump-button").on("click", function () {
    var jumpToPageInput = $("#jump-to-page");
    var pageNumber = parseInt(jumpToPageInput.val());

    var formData = new FormData(document.getElementById("filter-form"));
    // Parse the values
    var minPriceValue = parseFloat(
      $("#min_price_filter").val().replace(/\D/g, "")
    );
    var maxPriceValue = parseFloat(
      $("#max_price_filter").val().replace(/\D/g, "")
    );

    // Check if minPriceValue is a valid number
    if (!isNaN(minPriceValue)) {
      formData.set("min_price_filter", minPriceValue);
    } else {
      formData.set("min_price_filter", ""); // Set it to blank if it's not a valid number
    }

    // Check if maxPriceValue is a valid number
    if (!isNaN(maxPriceValue)) {
      formData.set("max_price_filter", maxPriceValue);
    } else {
      formData.set("max_price_filter", ""); // Set it to blank if it's not a valid number
    }

    // Validate that the entered page number is within the allowed range
    if (!isNaN(pageNumber) && pageNumber >= 1 && pageNumber <= total_pages) {
      // Handle jumping to the selected page (e.g., trigger a function to load that page)
      handlePaginationClick(pageNumber, formData);
    } else {
      // Show an error message or take appropriate action for invalid input
      alert(
        "Invalid page number. Please enter a number between 1 and " +
        total_pages +
        "."
      );
    }
  });
  // Attach event listener to form fields
  $(".filter-form input, .filter-form select").on("change", function () {
    updatePaginationLinks();
  });
});

function handlePaginationClick(page, formData) {
  $("#loading-overlay").show();
  var url = "/dashboard?page=" + page;

  // Include filter criteria in the URL
  var filters = $("#filter-form").serialize(); // Serialize the filter form
  url += "&" + filters; // Append filter criteria to the URL

  $.ajax({
    type: "POST",
    url: url,
    data: formData,
    contentType: false,
    processData: false,
    dataType: "json",
    success: function (data) {
      total_pages = data.pagination.pages;

      updateProperties(data);
      updatePaginationControls(
        data.pagination.paginationHTML,
        data.pagination.pages
      );
      updatePaginationLinks(); // Add this line to update the pagination links

      // Hide the loading indicator when the request is complete
      $("#loading-overlay").hide();

      // Clear the jump-to input field on success:
      $("#jump-to-page").val("");
    },
    error: function (error) {
      console.error("Error fetching properties:", error);
      // Hide the loading indicator when the request is complete
      $("#loading-overlay").hide();
    },
  });
}

// Function to update properties and pagination
function updateProperties(data) {
  // Update properties in #properties_table tbody
  var propertiesBody = $("#properties_table tbody");
  propertiesBody.empty();

  for (var i = 0; i < data.properties.length; i++) {
    var property = data.properties[i];
    var row = $("<tr>", {
      // class:
      // "m-0 p-0"
    });

    row.append(
      $("<td>").html(
        '<div class="form-check form-check-muted m-0">' +
        '<label class="form-check-label">' +
        '<input type="checkbox" class="form-check-input property-checkbox" data-property-id="' +
        property.id +
        '">' +
        '<i class="input-helper"></i>' +
        "</label>" +
        "</div>"
      )
    );

    // Property Description
    var propertyDesc = "";
    if (property.street_number) {
      propertyDesc += property.street_number + " ";
    }
    if (property.street_name) {
      propertyDesc += property.street_name + " ";
    }
    if (property.complex_number) {
      propertyDesc += property.complex_number + " ";
    }
    if (property.complex_name) {
      propertyDesc += property.complex_name;
    }

    if (propertyDesc === "") {
      propertyDesc = "No description available"; // Fallback text
    }

    // Wrap the property description in an anchor tag
    var propertyDescLink = $("<a>", {
      href: "/view_property/" + property.id, // Modify this URL as needed
      class: "clickable-property-desc p-1",
      text: propertyDesc,
    });

    var descriptionCell = $("<td>", {
      "data-column": "prop_desc",
      class: "p-1",
    }).append(propertyDescLink);

    row.append(descriptionCell);

    // Other columns
    var areaCell = $("<td>", {
      "data-column": "area",
      class: "p-1",
    }).text(property.area);
    row.append(areaCell);

    // Price column without decimals
    var priceFormatted = "R " + numberWithCommas(Math.floor(property.price));
    var priceCell = $("<td>", {
      class: "p-1",
      "data-column": "price", // Add the data-column attribute
    }).text(priceFormatted);
    row.append(priceCell);

    // Bedrooms column
    var bedroomsCell = $("<td>", {
      class: "p-1",
      "data-column": "bedrooms", // Add the data-column attribute
    }).text(property.bedrooms);
    row.append(bedroomsCell);

    // Bathrooms column
    var bathroomsCell = $("<td>", {
      class: "p-1",
      "data-column": "bathrooms", // Add the data-column attribute
    }).text(property.bathrooms);
    row.append(bathroomsCell);

    // Garages column
    var garagesCell = $("<td>", {
      class: "p-1",
      "data-column": "garages", // Add the data-column attribute
    }).text(property.garages);
    row.append(garagesCell);

    // P-24 Link
    var p24Link = $("<a>", {
      class: "btn btn-primary m-1 p-2",
      href: property.link,
      target: "_blank",
      text: property.link_display,
    });
    row.append($("<td>", {class: "p-1"}).append(p24Link));

    // Expandable columns
    row.append(
      $("<td>", {
        class: "p-1",
        "data-column": "swimming_pool", // Add the data-column attribute
      })
        .text(property.swimming_pool)
        .addClass("expandable-column")
    );

    row.append(
      $("<td>", {
        class: "p-1",
        "data-column": "garden_flat", // Add the data-column attribute
      })
        .text(property.garden_flat)
        .addClass("expandable-column")
    );

    row.append(
      $("<td>", {
        class: "p-1",
        "data-column": "study", // Add the data-column attribute
      })
        .text(property.study)
        .addClass("expandable-column")
    );

    row.append(
      $("<td>", {
        class: "p-1",
        "data-column": "ground_floor", // Add the data-column attribute
      })
        .text(property.ground_floor)
        .addClass("expandable-column")
    );

    row.append(
      $("<td>", {
        class: "p-1",
        "data-column": "pet_friendly", // Add the data-column attribute
      })
        .text(property.pet_friendly)
        .addClass("expandable-column")
    );

    propertiesBody.append(row);
  }
}

function handleFormSubmit() {
  var minPriceValue = parseFloat(
    $("#min_price_filter").val().replace(/\D/g, "")
  );
  var maxPriceValue = parseFloat(
    $("#max_price_filter").val().replace(/\D/g, "")
  );

  if (
    minPriceValue !== "" &&
    maxPriceValue !== "" &&
    parseInt(minPriceValue) > parseInt(maxPriceValue)
  ) {
    alert("Minimum price cannot be higher than maximum price.");
  } else {
    var formData = new FormData(); // Create a new FormData object
    formData.append(
      "street_name_filter",
      $('[name="street_name_filter"]').val()
    );
    formData.append(
      "complex_name_filter",
      $('[name="complex_name_filter"]').val()
    );

    if (!isNaN(minPriceValue)) {
      formData.append("min_price_filter", minPriceValue);
    }

    if (!isNaN(maxPriceValue)) {
      formData.append("max_price_filter", maxPriceValue);
    }

    formData.append("area_filter", $('[name="area_filter"]').val());
    formData.append("number_filter", $('[name="number_filter"]').val());
    formData.append("bedroom_filter", $('[name="bedroom_filter"]').val());
    formData.append("bathroom_filter", $('[name="bathroom_filter"]').val());
    formData.append("garages_filter", $('[name="garages_filter"]').val());
    formData.append("prop_type_filter", $('[name="prop_type_filter"]').val());
    formData.append("prop_category_filter", $('[name="prop_category_filter"]').val());
    formData.append("carports_filter", $('[name="carports_filter"]').val());
    formData.append("agent_filter", $('[name="agent_filter"]').val());
    formData.append("stand_area_filter", $('[name="stand_area_filter"]').val());
    formData.append("stand_area_select", $('[name="stand_area_select"]').val());
    formData.append("floor_area_filter", $('[name="floor_area_filter"]').val());
    formData.append("floor_area_select", $('[name="floor_area_select"]').val());

    // Handle checkboxes
    if ($("#study_filter").prop("checked")) {
      formData.append("study_filter", "true");
    }
    if ($("#swimming_pool_filter").prop("checked")) {
      formData.append("swimming_pool_filter", "true");
    }
    if ($("#ground_floor_filter").prop("checked")) {
      formData.append("ground_floor_filter", "true");
    }
    if ($("#garden_flat_filter").prop("checked")) {
      formData.append("garden_flat_filter", "true");
    }
    if ($("#pet_friendly_filter").prop("checked")) {
      formData.append("pet_friendly_filter", "true");
    }

    handlePaginationClick(1, formData); // Send the form data along with page number
  }
}

function updatePaginationLinks() {
  var formData = new FormData($(".filter-form")[0]); // Construct FormData object

  // Construct the URLSearchParams manually
  var params = [];
  formData.forEach(function (value, key) {
    params.push(key + "=" + encodeURIComponent(value));
  });
  var queryString = params.join("&");

  var paginationLinks = $(".dynamic-pagination-link");
  if (paginationLinks.length === 1) {
    var page = paginationLinks.data("page");
    var newHref = "/dashboard?page=" + page + "&" + queryString;
    paginationLinks.attr("href", newHref);
  } else {
    paginationLinks.each(function () {
      var page = $(this).data("page");
      var newHref = "/dashboard?page=" + page + "&" + queryString;
      $(this).attr("href", newHref);
    });
  }
}

function resetFilters() {
  // Reset filter input values
  $('[name="street_name_filter"]').val("");
  $('[name="complex_name_filter"]').val("");
  $('[name="number_filter"]').val("");
  $('[name="area_filter"]').val("");
  $('[name="max_price_filter"]').val(0); // Reset the value directly
  $('[name="min_price_filter"]').val(0); // Reset the value directly
  $('[name="bedroom_filter"]').val("");
  $('[name="bathroom_filter"]').val("");
  $('[name="garages_filter"]').val("");
  $('[name="agent_filter"]').val("");
  $('[name="carports_filter"]').val("");
  $("#study_filter").prop("checked", false);
  $("#swimming_pool_filter").prop("checked", false);
  $("#ground_floor_filter").prop("checked", false);
  $("#garden_flat_filter").prop("checked", false);
  $("#pet_friendly_filter").prop("checked", false);
  $('[name="prop_type_filter"]').val("");
  $('[name="prop_category_filter"]').val("");
  $('[name="stand_area_filter"]').val("");
  $('[name="floor_area_filter"]').val("");

  minPriceAutoNumeric.clear();
  maxPriceAutoNumeric.clear();

  $("#loading-overlay").show();
  // Make an AJAX request to clear filters and update the table
  $.ajax({
    url: "/dashboard", // Use the /dashboard route for clearing filters
    method: "POST",
    data: {
      reset_filters: true,
    },
    success: function (data) {
      // Update the table using the data received from the server
      updateProperties(data);
      // Generate new pagination HTML based on the updated data
      updatePaginationControls(
        data.pagination.paginationHTML,
        data.pagination.pages
      );
      // Clear the filter form inputs after successful response

      // Update the total_pages variable
      total_pages = data.pagination.pages;
      $("#total-pages").text(total_pages);

      $("#filter-form")[0].reset();
      // Clear the selected areas in the dropdown for area filters
      $(".js-example-basic-multiple").val([]); // Set an empty array to clear selection
      $(".js-example-basic-multiple").trigger("change"); // Refresh the dropdown to clear selected values
      $("#jump-to-page").val(""); // Clear jump-to page
      // Hide the loading indicator when the request is complete
      $("#loading-overlay").hide();
    },
    error: function (error) {
      console.error("Error clearing filters:", error);
      // Hide the loading indicator when the request is complete
      $("#loading-overlay").hide();
    },
  });
}

function numberWithCommas(number) {
  return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function updatePaginationControls(paginationHTML) {
  var newPaginationContainer = $("#new-pagination-container");
  newPaginationContainer.empty().append(paginationHTML);

  // Update pagination links
  newPaginationContainer
    .find(".pagination-link")
    .addClass("dynamic-pagination-link");

  // Update the total number of pages
  $("#total-pages").text(total_pages);
}
