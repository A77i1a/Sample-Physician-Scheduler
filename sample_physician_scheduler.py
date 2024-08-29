from ortools.sat.python import cp_model  # Import the CP-SAT solver from OR-Tools

def main():
    # Define problem parameters
    num_physicians = 10  # Total number of physicians
    num_shifts = 3  # Number of shifts per day
    num_days = 7  # Number of days in the schedule
    all_physicians = range(num_physicians)  # Range of physician indices
    all_shifts = range(num_shifts)  # Range of shift indices
    all_days = range(num_days)  # Range of day indices

    # Create the constraint programming model
    model = cp_model.CpModel()

    # Create shift variables: shifts[(p, d, s)] = 1 if physician p works shift s on day d
    shifts = {}
    for p in all_physicians:
        for d in all_days:
            for s in all_shifts:
                shifts[(p, d, s)] = model.NewBoolVar(f'shift_p{p}_d{d}_s{s}')

    # Add constraints to the model

    # 1. Coverage Requirements
    for d in all_days:
        for s in all_shifts:
            # Ensure at least one physician is on duty for each shift
            model.Add(sum(shifts[(p, d, s)] for p in all_physicians) >= 1)
        
        # Ensure at least two physicians during peak hours (shifts 0 and 1)
        for s in [0, 1]:
            model.Add(sum(shifts[(p, d, s)] for p in all_physicians) >= 2)

    # 2. Shift Length and Rest Periods
    for p in all_physicians:
        for d in all_days:
            # Ensure no physician works more than one shift per day
            model.Add(sum(shifts[(p, d, s)] for s in all_shifts) <= 1)
            
            # Simplified 10-hour rest period: can't work night shift and morning shift next day
            if d < num_days - 1:
                model.Add(shifts[(p, d, 2)] + shifts[(p, (d+1)%7, 0)] <= 1)

    # 3. Fairness - Equal number of night shifts
    night_shifts = {}
    for p in all_physicians:
        # Count night shifts for each physician
        night_shifts[p] = sum(shifts[(p, d, 2)] for d in all_days)
    
    # Ensure all physicians have the same number of night shifts
    for p1 in all_physicians:
        for p2 in all_physicians:
            if p1 < p2:
                model.Add(night_shifts[p1] == night_shifts[p2])

    # 4. Senior Physician Rules
    for d in all_days:
        # Prevent Dr. Smith (physician 8) from working night shifts
        model.Add(shifts[(8, d, 2)] == 0)
        # Prevent Dr. Jones (physician 9) from working night shifts
        model.Add(shifts[(9, d, 2)] == 0)

    # 5. Weekend Rules
    for p in all_physicians:
        for s in all_shifts:
            # Ensure same assignment for Saturday (day 5) and Sunday (day 6)
            model.Add(shifts[(p, 5, s)] == shifts[(p, 6, s)])

    # Objective: Maximize fairness by minimizing variance in total shifts
    total_shifts = {}
    for p in all_physicians:
        # Count total shifts for each physician
        total_shifts[p] = sum(shifts[(p, d, s)] for d in all_days for s in all_shifts)

    # Minimize the sum of squared differences in total shifts between all pairs of physicians
    model.Minimize(sum((total_shifts[p1] - total_shifts[p2]) * (total_shifts[p1] - total_shifts[p2])
                       for p1 in all_physicians for p2 in all_physicians if p1 < p2))

    # Create a solver and solve the model
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # Print the solution if one is found
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("Solution found:")
        for d in all_days:
            print(f"Day {d+1}:")
            for s in all_shifts:
                print(f"  Shift {s+1}:", end=" ")
                for p in all_physicians:
                    if solver.Value(shifts[(p, d, s)]) == 1:
                        print(f"P{p+1}", end=" ")
                print()
            print()
    else:
        print("No solution found.")

    # Print solver statistics
    print("\nStatistics")
    print(f"  - Status    : {solver.StatusName(status)}")
    print(f"  - Conflicts : {solver.NumConflicts()}")
    print(f"  - Branches  : {solver.NumBranches()}")
    print(f"  - Wall time : {solver.WallTime()} s")

if __name__ == "__main__":
    main()  # Run the main function when the script is executed