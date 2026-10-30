import {useState} from 'react'
import {useMutation, useQuery, useQueryClient} from '@tanstack/reacyt-query'
import {Sparkles, RsearchCw,XCircle, CheckCircle2, Clock, AlertCircle, Loader2} from 'lucide-react'
import api from '../services/api'
const ACTIVE =['queued','running']

const styles= {
  queued: 'bg-yellow-100 text-yellow-800',
  running: 'bg-blue-100  text-blue-800' 
}