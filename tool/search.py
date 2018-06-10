def print_results(results, n=7):
    for i in results:
        print ('\n\t\t', i)
        for j in sorted(results[i], key=results[i].get, reverse=True)[:n]:
            print (j, results[i][j])
            
            
