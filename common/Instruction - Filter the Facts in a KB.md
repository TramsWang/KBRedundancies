# Instruction: Filter the Facts within an RDF KB

This instruction states the method to filter and reserve only the facts within an RDF KB.

## 1. Filter out non-factual statements

Use blacklists of predicate IRIs to throw away non-factual statements.
Blacklists for certain namespaces are listed as follows:

1. RDFS:
    ```
    rdfs:domain
    rdfs:range
    rdfs:subClassOf
    rdfs:subPropertyOf
    rdfs:label
    rdfs:comment
    rdfs:isDefinedBy
    rdfs:seeAlso
    ```
2. OWL:
   - All blank nodes that has an OWL class as its type should be removed, and so should the statements involving the blank nodes.
   That is, let `_:x` be a blank node, it should be removed from the RDF graph, together with all arcs from or to it:
   ```
   _:x rdf:type owl:*
   ```

In a concrete dataset, some properties that serve meta-info purposes should also be excluded:

1. YAGO:
   ```
   describes
   foundIn
   extractedBy
   context
   ```

## 2. Name blank nodes
Normally, blank nodes should have been given a locally unique name in the RDF KBs.
**IF NOT**, they should be assigned by a local IRI, so that different blank nodes will not be mapped to the same number.
In this project, we should assign a name of the following format for each blank node: `_:<ID>`.
E.g., `_:23`, `_:2048`.

## 3. Convert type statements
All resources that have a type should be converted to a unary predicate named by the type.
That is, let `R` be a resource IRI, `T` be a type IRI, the following RDF statement:
```
R rdf:type T
```
should be converted to the following predicate (denoted by the first-order logic convention):
```
T(R)
```
For example, `SJTU rdf:type University` should be converted to `University(SJTU)`.
According to the language specification of RDF and RDFS, there is no other reserved vocabulary that is used for the same purpose.

## 4. Convert normal statements
Other statements irrelevant to types, i.e., the predicate is not `rdf:type`, should be converted to binary predicates.
Let `S` and `O` be two resource IRIs, `P` be a predicate IRI, the following RDF statement:
```
S P O
```
should be converted to the following predicate (denoted by the first-order logic convention):
```
P(S, O)
```

## 5. Use namespace prefixes
For simplicity, all IRIs should use namespace prefixes if possible.
For example, the IRI `http://www.w3.org/1999/02/22-rdf-syntax-ns#type` should be written as `rdf:type`.
All the mappings of the namespaces should be stored in a file named `namespaces.tsv`, each line of which contains two columns separated by `\t`, where the first is the namespace prefix, and the second is the full IRI the prefix stands for.
For example, the followings show an example of the file:
```
rdf:	http://www.w3.org/1999/02/22-rdf-syntax-ns#
rdfs:	http://www.w3.org/2000/01/rdf-schema#
owl:	http://www.w3.org/2002/07/owl#
xsd:	http://www.w3.org/2001/XMLSchema#
```

## 6. Dump by the numerated format
All converted predicates should be stored in the local file system by the numerated KB format.