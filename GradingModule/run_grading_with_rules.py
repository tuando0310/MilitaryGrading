import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'src'))
from services.io_service import IOService
from services.grading_service import GradingService
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR = BASE_DIR / 'output'
CONFIG_DIR = BASE_DIR / 'config'
USER_FILE = DATA_DIR / 'aligned_grading_data.json'
MODEL_FILE = DATA_DIR / 'model_data.json'
MAPPING_FILE = OUTPUT_DIR / 'dtw_mapping_result.json'
RULES_FILE = CONFIG_DIR / 'rules.json'
def main():
    io = IOService()
    grader = GradingService()
    try:
        # Load Data
        print("Loading data...")
        user_data = io.load_json(USER_FILE)
        model_data = io.load_json(MODEL_FILE)
        mapping_obj = io.load_json(MAPPING_FILE)
        rules = io.load_json(RULES_FILE)
        
        user_seq = [item['data'] for item in user_data]
        model_seq = [item['data'] for item in model_data]
        
        if isinstance(mapping_obj, dict): mapping_arr = mapping_obj['mapping']
        else: mapping_arr = mapping_obj
        # Run Grading
        print("Evaluating with rules...")
        detailed_results = grader.evaluate_performance_with_rules(
            user_seq, model_seq, mapping_arr, rules
        )
        # Summary
        total_frames = len(detailed_results)
        # Pass logic could be defined in rules or config, here assuming score > 50
        pass_point = rules.get('pass_point', 50)
        passing_frames = sum(1 for r in detailed_results if r['score'] >= pass_point)
        
        print(f"[RESULT] Passed: {passing_frames}/{total_frames} ({passing_frames/total_frames*100:.2f}%)")
        # Save Report
        final_report = {
            "summary": {
                "total_frames": total_frames,
                "passed": passing_frames,
                "pass_point": pass_point
            },
            "frames_detail": detailed_results
        }
        
        io.save_json(final_report, OUTPUT_DIR / 'grading_report_rules.json')
        print(f"Report saved to {OUTPUT_DIR / 'grading_report_rules.json'}")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
if __name__ == "__main__":
    main()