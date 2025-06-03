(define-module (pln-bio combo-preprocess)
    #:use-module (opencog)
    #:use-module (opencog bioscience)
    #:use-module (opencog exec)
    #:use-module (srfi srfi-1))

(define-public (get-top-genes n)
    (let* ((gene-preds (filter (lambda (p) 
                (and (not (string=? "outcome" (cog-name p))) (not (string-prefix? "brca:" (cog-name p))))) (cog-get-atoms 'PredicateNode)))
                
           (sorted-scores (sort (map (lambda (pred) (cons (GeneNode (cog-name pred)) (get-gene-score pred))) gene-preds)  compare?))
           (top-genes (map (lambda (p) (car p)) sorted-scores)))
           
        (take top-genes n)))
 
(define (get-containers gene-pred)
    ;;Get the models that where gene-pred occurs in
        (cog-value->list (cog-execute! 
            (MaximalJoin
                (TypedVariable (Variable "$x") (Signature gene-pred))
                (ReplacementLink (Variable "$x") gene-pred)))))

(define (get-f1-score ln)
        (let* ((model (gar ln))
            (recall (cog-mean (car (cog-outgoing-set (cog-execute! 
            (Bind 
                (Present 
                    (ImplicationLink 
                        (Variable "$a")
                        model))                       
                (ImplicationLink 
                        (Variable "$a")
                        model)))))))
            (precision (cog-mean (car (cog-outgoing-set (cog-execute! 
            (Bind 
                (Present 
                    (ImplicationLink 
                        model
                        (Variable "$a")))                       
                (ImplicationLink 
                        model
                        (Variable "$a")))))))))           
            (* 2 (/ (* recall precision) (+ recall precision)))))

(define (get-gene-score gene-pred)
    ;;Given a gene with PredicateNode type it will extract
    ;; the models that contain gene-pred and return the sum of their f1 scores

    (let* ((eqv-lns (get-containers gene-pred))
           (f1-scores (map get-f1-score eqv-lns)))   
        (fold + 0 f1-scores)))

(define (compare? x y) (if (< (cdr x) (cdr y)) #f #t))