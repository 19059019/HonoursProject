var options = {}

document.addEventListener('DOMContentLoaded', function () {
    var elems = document.querySelectorAll('select');
    var instances = M.FormSelect.init(elems, options);
});

window.onload = function () {
    var checkboxes = document.getElementsByTagName('input');
    for (var i = 0; i < checkboxes.length; i++) {
        if (checkboxes[i].type == 'checkbox') {
            checkboxes[i].checked = false;
        }
    }
    makeSubmissionNotRequired();
    makeEnvironmentNotRequired();
    $(document).ready(function () {
        $('input#input_text, textarea#input_text').characterCounter();
    });

    $("input[name=shared_folder_checkbox]").attr("disabled", true)

    $('#download_during').hide();
    $(".internet_restriction").hide();
    $(".resubmissions").hide();
    $(".resub-range").hide();
    $(".virtual_machine").hide();
    $(".time_limit_div").hide();
    $(".file-field").hide();
    $(".submission").hide();
    $(".git").hide();
    $(".environment").hide();
    $(".button").hide();
    $('#whitelist_div').hide();

    $("input[name=time_limit_checkbox]").click(function () {
        $('.time_limit_div')[this.checked ? "show" : "hide"]();
        if (this.checked) {
            $("input[name=time_limit]").prop('required', true);
        } else {
            $("input[name=time_limit]").prop('required', false);
        }
    });
    $("input[name=internet_restriction]").click(function () {
        $('.internet_restriction')[this.checked ? "show" : "hide"]();
    });
    $("input[name=allow_resubmissions]").click(function () {
        $('.resubmissions')[this.checked ? "show" : "hide"]();
        if (this.checked) {
            $("input[name=resubmissions]").prop('required', true);
        } else {
            $("input[name=resubmissions]").prop('required', false);
        }
    });
    
    $("input[name=limit_resubmissions]").click(function () {
        $('.resub-range')[this.checked ? "show" : "hide"]();
    });

    $("input[name=virtual_machine_checkbox]").click(function () {
        $('.virtual_machine')[this.checked ? "show" : "hide"]();
    });
    $('input[name=whitelist_box]').click(function () {
        $('#whitelist_div')[this.checked ? "show" : "hide"]();
        if (this.checked) {
            $("input[name='whitelist_websites']").prop('required', true);
        } else {
            $("input[name='whitelist_websites']").prop('required', false);
        }
    });

    $('input[name=ci_test]').click(function () {
        $('div[name=requirements_file_field]')[this.checked ? "show" : "hide"]();
        $('div[name=test_file_field]')[this.checked ? "show" : "hide"]();
        if (this.checked) {
            $("input[name=requirements]").prop('required', true);
            $("input[name=test_file]").prop('required', true);
        } else {
            $("input[name=test_file]").prop('required', false);
            $("input[name=requirements]").prop('required', false);
        }

    });

    $('input[name=submission_checkbox]').click(function () {
        $('div[name=submission_file_field]')[this.checked ? "show" : "hide"]();
        $('#download_during')[this.checked ? "show" : "hide"]();
        if (this.checked) {
            $("input[name=submission_file]").prop('required', true);
            $("input[name=shared_folder_checkbox]").removeAttr("disabled")
        } else {
            $("input[name=submission_file]").prop('required', false);
            $("input[name=shared_folder_checkbox]").attr("disabled", true)
        }

    });
    $('#submission').click(function () {
        $('.submission')[this.checked ? "show" : "hide"]();
        $('.button')[this.checked ? "show" : "hide"]();
        if (this.checked) {
            makeSubmissionRequired();
        } else {
            makeSubmissionNotRequired();
        }
    });
    $('#git').click(function () {
        $('.submission')[this.checked ? "show" : "hide"]();
        $('.git')[this.checked ? "show" : "hide"]();
        $('.button')[this.checked ? "show" : "hide"]();
        if (this.checked) {
            makeSubmissionRequired();
        } else {
            makeSubmissionNotRequired();
        }
    });
    $('#environment').click(function () {
        $('.environment')[this.checked ? "show" : "hide"]();
        $('.button')[this.checked ? "show" : "hide"]();
        if (this.checked) {
            makeEnvironmentRequired();
        } else {
            makeEnvironmentNotRequired();
        }
    });

    $('input[name=inetkey]').click(function () {
        if (this.checked) {
            $('input[name=sun]').prop("checked", false);
            $('input[name=sun]').attr("disabled", true);
            $('input[name=whitelist_box]').prop("checked", false);
            $('input[name=whitelist_box]').attr("disabled", true);
        } else {
            $('input[name=sun]').removeAttr("disabled");
            $('input[name=whitelist_box]').removeAttr("disabled");
        }
    });
}

function makeSubmissionRequired() {
    $("input[name=start_date]").prop('required', true);
    $("input[name=end_date]").prop('required', true);
}

function makeSubmissionNotRequired() {
    $("input[name=start_date]").prop('required', false);
    $("input[name=end_date]").prop('required', false);
}

function makeEnvironmentRequired() {
    if ($('input[name=time_limit_checkbox]').checked) {
        $("input[name=time_limit]").prop('required', true);
    } else {
        $("input[name=time_limit]").prop('required', false);
    }
}

function makeEnvironmentNotRequired() {
    $("input[name=time_limit]").prop('required', false);
}
