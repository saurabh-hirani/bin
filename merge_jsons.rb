#!/usr/bin/env ruby

require 'json'
require 'deep_merge'

def merge_json_files(f1, f2, flat_ds_to_merge)
  f1_ds = JSON.parse(File.read(f1))
  f2_ds = JSON.parse(File.read(f2))

  curr_ds = f1_ds
  nested_keys = flat_ds_to_merge.split('.')

  nested_keys.each do |k|
    curr_ds = curr_ds[k]
  end

  if curr_ds.kind_of?(Array)
    curr_ds.each do |ds_elem|
      if ds_elem.kind_of?(Array)
        raise "ERROR: Nested array in #{f1}"
      end
      ds_elem.deep_merge!(f2_ds, :merge_nested_arrays => true)
    end
  else
    curr_ds.deep_merge!(f2_ds, :merge_nested_arrays => true)
  end
  return f1_ds
end

src_file = ARGV[0]
merge_file = ARGV[1]
flat_ds_to_merge = ARGV[2]

files_to_merge = []

if File.directory?(src_file)
  files_to_merge = Dir["#{src_file}/*.json"]
elsif File.file?(src_file)
  files_to_merge = [src_file]
elsif src_file.include?(' ')
  files_to_merge = src_file.split(' ')
else
  files_to_merge = Dir["#{src_file}"]
end

files_to_merge.each do |filepath|
  puts "STATUS: Merging #{filepath} and #{merge_file}"
  merged_ds = merge_json_files filepath, merge_file, flat_ds_to_merge
  reformatted = JSON.pretty_generate(merged_ds)
  File.open(filepath, 'w') { |f| f.puts reformatted }
end
