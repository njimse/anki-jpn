function insert_ending_spans(dict_form, conjugation) {
    if (dict_form == conjugation) {
        return conjugation;
    }

    var split_index = Math.min(dict_form.length, conjugation.length);
    while (split_index > 0) {

        if (dict_form.slice(0,split_index) != conjugation.slice(0, split_index)) {
            split_index -= 1;
        } else {
            break;
        }
    }

    var new_conjugation = "";
    var open_ruby_tags = (conjugation.slice(split_index).match(/<ruby>/g) || []).length;
    var close_ruby_tags = (conjugation.slice(split_index).match(/<\/ruby>/g) || []).length;
    var open_rt_tags = (conjugation.slice(split_index).match(/<rt>/g) || []).length;
    var close_rt_tags = (conjugation.slice(split_index).match(/<\/rt>/g) || []).length;
    if (open_ruby_tags == close_ruby_tags) {
        // The split is not within a ruby tag, just use the split index as-is
        new_conjugation = conjugation.slice(0,split_index) + "<span class=ending>" + conjugation.slice(split_index) + "</span>";
    } else if (open_rt_tags == close_rt_tags) {
        // The split is inside a ruby tag, but outside of the rt tags. Assume the rt has changed, and keep
        // moving the split index until it is to the left of the current ruby section
        while (split_index > 0) {
            if (open_ruby_tags != close_ruby_tags) {
                split_index -= 1;
            } else {
                break
            }
        }
        new_conjugation = conjugation.slice(0,split_index) + "<span class=ending>" + conjugation.slice(split_index) + "</span>";
    } else {
        // The split is inside an rt tag. Locate the closing rt tag so that we can insert a span within the rt
        var rt_close_offset = conjugation.slice(split_index).indexOf("</rt>");
        var new_base = conjugation.slice(0, split_index) + "<span class=ending>" + conjugation.slice(split_index, split_index + rt_close_offset) + "</span>";
        var ruby_close_offset = conjugation.slice(split_index+rt_close_offset).indexOf("</ruby>") + "</ruby>".length;
        var new_ending = conjugation.slice(split_index + rt_close_offset, split_index+rt_close_offset + ruby_close_offset) + "<span class=ending>" + conjugation.slice(split_index+rt_close_offset + ruby_close_offset) + "</span>";
        new_conjugation = new_base + new_ending;
    }
    return new_conjugation;
}