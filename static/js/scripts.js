/*!
    * Start Bootstrap - SB Admin v7.0.7 (https://startbootstrap.com/template/sb-admin)
    * Copyright 2013-2023 Start Bootstrap
    * Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-sb-admin/blob/master/LICENSE)
    */
    // 
// Scripts
// 

window.addEventListener('DOMContentLoaded', event => {

    // Toggle the side navigation
    const sidebarToggle = document.body.querySelector('#sidebarToggle');
    if (sidebarToggle) {
        // Uncomment Below to persist sidebar toggle between refreshes
        if (localStorage.getItem('sb|sidebar-toggle') === 'true') {
            document.body.classList.toggle('sb-sidenav-toggled');
        }
        sidebarToggle.addEventListener('click', event => {
            event.preventDefault();
            document.body.classList.toggle('sb-sidenav-toggled');
            localStorage.setItem('sb|sidebar-toggle', document.body.classList.contains('sb-sidenav-toggled'));
        });
    }

});




// script for the station drop down menu on dash page

const inputField = document.getElementById("search");
const dropdown = document.querySelector(".stations-dropdown");
const items = document.querySelectorAll(".dropdown-station");

// Show dropdown when input is focused
inputField.addEventListener("focus", function () {
    dropdown.style.display = "block";
});

// Hide dropdown if clicked outside
document.addEventListener("click", function (event) {
    if (!inputField.contains(event.target) && !dropdown.contains(event.target)) {
        dropdown.style.display = "none";
    }
});



// Filter the dropdown items based on input
function filterList() {
    let inputValue = inputField.value.toLowerCase();
    let hasMatch = false;

    items.forEach(item => {
        if (item.textContent.toLowerCase().includes(inputValue)) {
            item.style.display = "block";
            hasMatch = true;
        } else {
            item.style.display = "none";
        }
    });

    dropdown.style.display = hasMatch ? "block" : "none";
}

// Handle selection from dropdown
items.forEach(item => {
    item.addEventListener("click", function () {
        inputField.value = item.textContent; // Set the input value
        dropdown.style.display = "none"; // Hide the dropdown after selection
    });
});








function refreshLinesData() {
    $.ajax({
        url: "/get-processed-data/lines",  
        type: "GET",
        success: function(response) {
            $("#shift_in_session").text(response.shift_in_session);
            $("#station_in_session").text(response.station_in_session);
            $("#selected_date").text(response.selected_date);
            // $("#operator_name").text(response.operator_name);
            $("#shift_name").text(response.shift_name);
            $("#current_year").text(response.current_year);

            $.each(response.data, function(lineKey, lineValue) {
                // Ensure the line exists; if not, create it
                if ($("#line_" + lineKey).length === 0) {
                    $("#data-container").append(`<div class="col-xl-6 col-lg-6">
                                                    <div class="card shadow h-30 py-1 mb-1">
                                                        <div class="card-body">
                                                            <div class="row no-gutters align-items-center">
                                                                <div class="col mr-2">
                                                                    <div class="text font-weight-bold text-primary text-uppercase mb-1">
                                                                        <div id="line_${lineKey}"> ${lineKey}
                                                                            
                                                                        </div>
                                                                    
                                                                    </div>

                                                                    </div>
                                                                        
                                                                </div>
                                                                
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                                    `);
                }
                
                 // Convert stations object to array and sort by performance (stationValue[1])
                let sortedStations = Object.entries(lineValue).sort((a, b) => a[1][1] - b[1][1]);

                // Clear existing stations before adding sorted ones
                $("#line_" + lineKey).empty().append(`<p>${lineKey}</p>`);

                // Loop through stations inside each line
                // $.each(lineValue, function(stationKey, stationValue)
                sortedStations.forEach(([stationKey, stationValue]) => 
                {
                    let stationId = `station_${lineKey}_${stationKey}`;
                    let stationPerId = stationId + "_per";
                    let stationTprodId = stationId + "_tprod";
                    let stationTcardId = stationId + "_card";
                    let performanceClass = "";
                    if (stationValue[1] == 0) {
                        performanceClass = "bg-secondary text-white";  
                    } else if (0 < stationValue[1] && stationValue[1] < 55) {
                        performanceClass = "bg-danger text-white"; 
                    } else if (55 <= stationValue[1] && stationValue[1] < 85) {
                        performanceClass = "bg-warning text-white";
                    } else if (stationValue[1] >= 85) {
                        performanceClass = "bg-success text-white";
                    }
                    // Check if the station already exists in the DOM
                    if ($("#" + stationId).length === 0) {
                        // If station is new, append it to the line div
                        $("#line_" + lineKey).append(`
                                                    <div id="${stationTcardId}" class="card m-2 fit-content ${performanceClass} d-inline-block">
                                                        <a href="http://127.0.0.1:5000/dash?date={{session['date']}}&shift_name={{shift_name}}&station=${stationKey}">
                                                        <div class="card-body station-title-text text-white" id="${stationId}">${stationKey}</div>
                                                        <div class="card-footer d-flex align-items-center justify-content-between">
                                                            <p class="small text-white stretched-link"> <span id="${stationPerId}"> ${stationValue[1]} </span> % / 
                                                            <span id="${stationTprodId}">${stationValue[0]}</span>Ps</p>
                                                        </div>
                                                        </a>
                                                    </div>
                                                    `);
                    
                    } else {
                        // If station already exists, update the values
                        $("#" + stationPerId).text(stationValue[1]);
                        $("#" + stationTprodId).text(stationValue[0]);
                         // Change the background color dynamically based on performance
                         let stationDiv = $("#" + stationTcardId);
                        // stationDiv.removeClass("bg-success bg-danger bg-secondary bg-warning").addClass(performanceClass);
                        stationDiv.attr("class", `card m-2 fit-content ${performanceClass} d-inline-block`);
                    }
            });
            });
            


            // $.each(response.data, function(lineKey, lineValue) {
            //     // Update each line
            //     $("#line_" + lineKey).text(lineKey);
    
            //     // Loop through lineValue inside each line
            //     $.each(lineValue, function(stationKey, stationValue) {
            //         $("#station_" + lineKey + "_" + stationKey).text(stationKey);
            //         $("#station_" + lineKey + "_" + stationKey + "_per").text(stationValue[1]);
            //         $("#station_" + lineKey + "_" + stationKey + "_tprod").text(stationValue[0]);
            //     });
            // });

        },
        error: function() {
            alert("Failed to fetch updated data.");
        }
    });
}

// // Auto-refresh every 10 seconds
// setInterval(refreshData, 1000);