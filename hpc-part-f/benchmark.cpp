#include <iostream>
#include <iomanip>
#include <cstdint>
#include <omp.h>
#include "src-openmp/datasets.cpp"
#include "src-openmp/losses.cpp"
#include "src-openmp/metrics.cpp"
#include "src-openmp/tree_node.cpp"
#include "src-openmp/decision_tree.cpp"
#include "src-openmp/random_forest.cpp"
int main(int argc, char** argv) {
    if (argc != 3) return 2;
    int ntree = std::stoi(argv[1]), threads = std::stoi(argv[2]);
    if (ntree < 1 || threads < 1 || threads > 4) return 2;
    omp_set_dynamic(0);
    omp_set_num_threads(threads);
    omp_set_max_active_levels(1);
    int actual = 0;
    #pragma omp parallel
    {
        #pragma omp single
        actual = omp_get_num_threads();
    }
    DataLoader loader = DataLoader("../data/sonar.all-data.numerical.csv");
    DataFrame df = loader.load();
    auto split = df.train_test_split(0.2, 1337);
    DataFrame train = split[0], test = split[1];
    double start = omp_get_wtime();
    RandomForest rf(train,ntree,false,"gini_impurity",-1,-1,-1,3,-1,69);
    double elapsed = omp_get_wtime() - start;
    if (rf.getNumTrees() != ntree || actual != threads) return 3;
    auto predictions = rf.predict(&df);
    uint64_t hash = 1469598103934665603ULL;
    for (double v : predictions.vector()) { hash ^= static_cast<uint64_t>(v); hash *= 1099511628211ULL; }
    std::cout << "RESULT " << ntree << " " << threads << " " << actual << " "
              << std::setprecision(12) << elapsed << " " << hash << " "
              << accuracy(test.col(-1), rf.predict(&test)) << std::endl;
}
