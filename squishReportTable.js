/* 
 * File Name: squishReportTable.js
 * Author: Joshua Niehus
 * Date: 10/29/2011
 * 
 * Description: jQuery script to express the behaviour of the report table
 */

// navigates to hovered testcase's details html
function navigate()
{
    var testCase = $(this).find("td.tcName").text();
    testCase += "_details.html";
    window.open(testCase);
}

// normalizer for next and previous operations
var currentCount = -1;

$(document).ready(function(){   
    // set relative heights of table containers, this will keep nav buttons on details table to stay visible
    $('div.scroll').css('height', function() {
        return ($(window).height() * 0.85);
    });    
    
    // interactive mouse over
    $('tr').hover(function() {
        $(this).addClass('zebraHover');           
    },  function() {
        $(this).removeClass('zebraHover');
    });
    
    // expand/collapse testcase behaviour
    $('tr.testcase').click(navigate);

    var defects = $('td.defect');    
    // goto next defect (wrap to first)
    $('#next').click(function () {
        currentCount++;
        if (currentCount >= defects.length) {
            currentCount = 0;
        }
        $('div.scroll').scrollTo(defects[currentCount]);
    });
    
    // goto previous defect (wrap to last)
    $('#previous').click(function () {
        currentCount--;
        if (currentCount < 0) {
            currentCount = (defects.length - 1);
        }
        $('div.scroll').scrollTo(defects[currentCount]);
    });    
});
