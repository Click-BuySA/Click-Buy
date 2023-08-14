function resetFilters() {
    document.getElementById("street_name_filter").value = "";
    document.getElementById("complex_name_filter").value = "";
    document.getElementById("number_filter").value = "";
    document.getElementById("area_filter").value = "";
    document.getElementById("max_price_filter").value = "";
    document.getElementById("bedroom_filter").value = "";
    document.getElementById("min_price_filter").value = "";
    document.getElementById("bathroom_filter").value = "";
    document.getElementById("garages_filter").value = "";
    document.getElementById("swimming_pool_filter").value = "";
    document.getElementById("garden_flat_filter").value = "";

      // Submit the form to clear the filters
    document.getElementById("filter-form").submit();
  }