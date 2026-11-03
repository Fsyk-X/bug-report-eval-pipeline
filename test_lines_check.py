from Capstone import check_report

fake_str = '''BUG-001 : "Ray Tracing Settings crash in Graphics menu when toggled On, causing complete program failure with 100% reproducibility (5 of 5 attempts, 5 times seen). Severity A, fixed in build v245.01, Status Closed(Fixed).'''
print(check_report(fake_str))