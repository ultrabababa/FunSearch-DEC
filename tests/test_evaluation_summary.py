from tools.compare_runs import summarize


def test_summarize_counts_failure_reasons(tmp_path):
    csv_path = tmp_path / "merged.csv"
    csv_path.write_text(
        "prompt_round,sample_index,sample_order,score,has_score,accepted_for_eval,failure_reason,prompt_file,raw_file,trimmed_file,raw_length,trimmed_length,function\n"
        "1,1,2,-220.1,True,True,,a,b,c,1,1,f\n"
        "1,2,3,,False,True,eval_failed_unknown,a,b,c,1,1,f\n"
        "1,3,4,,False,False,rejected_pre_eval,a,b,c,1,1,f\n",
        encoding="utf-8",
    )

    s = summarize(csv_path)
    assert s["total_rows"] == 3
    assert s["scored_rows"] == 1
    assert s["failed_rows"] == 2
    assert s["dedup_hits"] == 1
    assert s["eval_failed"] == 1


def test_summarize_uses_status_field_for_eval_failed_count(tmp_path):
    csv_path = tmp_path / "merged.csv"
    csv_path.write_text(
        "prompt_round,sample_index,sample_order,score,has_score,accepted_for_eval,failure_reason,status,prompt_file,raw_file,trimmed_file,raw_length,trimmed_length,function\n"
        "1,1,2,,False,True,dedup_intercepted,DEDUP_INTERCEPTED,a,b,c,1,1,f\n"
        "1,2,3,,False,True,eval_failed_unknown,EVAL_FAILED,a,b,c,1,1,f\n",
        encoding="utf-8",
    )

    s = summarize(csv_path)
    assert s["dedup_hits"] == 1
    assert s["eval_failed"] == 1


def test_summarize_to_target_ignores_rows_without_valid_sample_order(tmp_path):
    csv_path = tmp_path / "merged.csv"
    csv_path.write_text(
        "prompt_round,sample_index,sample_order,score,has_score,accepted_for_eval,failure_reason,status,sample_time,evaluate_time,prompt_file,raw_file,trimmed_file,raw_length,trimmed_length,function\n"
        "1,1,, -100.0,True,True,,SUCCESS,1.0,1.0,a,b,c,1,1,f\n"
        "1,2,2,-220.0,True,True,,SUCCESS,1.0,1.0,a,b,c,1,1,f\n",
        encoding="utf-8",
    )

    s = summarize(csv_path, target_score=-150.0)
    assert s["target_reached"] is False
    assert s["calls_to_target"] is None


def test_summarize_to_target_uses_strict_order_and_counts_from_reached_rows(tmp_path):
    csv_path = tmp_path / "merged.csv"
    csv_path.write_text(
        "prompt_round,sample_index,sample_order,score,has_score,accepted_for_eval,failure_reason,status,sample_time,evaluate_time,prompt_file,raw_file,trimmed_file,raw_length,trimmed_length,function\n"
        "1,1,1,-300.0,True,True,,SUCCESS,2.0,3.0,a,b,c,1,1,f\n"
        "1,2,2,,False,False,rejected_pre_eval,DEDUP_INTERCEPTED,2.0,0.0,a,b,c,1,1,f\n"
        "1,3,3,-200.0,True,True,,SUCCESS,2.0,4.0,a,b,c,1,1,f\n",
        encoding="utf-8",
    )

    s = summarize(csv_path, target_score=-250.0)
    assert s["target_reached"] is True
    assert s["calls_to_target"] == 3
    assert s["sandbox_evals_to_target"] == 2
    assert s["pipeline_time_to_target_sec"] == 13.0
